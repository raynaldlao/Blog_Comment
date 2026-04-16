import os

from pytestarch import Rule, get_evaluable_architecture


class TestArchitecture:
    """
    Architectural test suite to enforce Hexagonal Architecture constraints.
    The architecture graph is evaluated once during setup to optimize performance.
    """

    @classmethod
    def setup_class(cls):
        """
        Set up the evaluable architecture graph and dynamically discover
        the base module prefix.
        """
        root_dir = os.getcwd()
        src_path = os.path.abspath("src")
        cls.evaluable = get_evaluable_architecture(root_dir, src_path)
        cls.all_nodes = [str(node) for node in cls.evaluable._graph.nodes]

        base_prefix = ""
        for node in cls.all_nodes:
            if ".src.application.domain" in node:
                base_prefix = node.split(".src.application.domain")[0] + ".src"
                break

        cls.BASE = base_prefix if base_prefix else "Blog_Comment.src"
        cls.L_APP = f"{cls.BASE}.application"
        cls.L_DOMAIN = f"{cls.BASE}.application.domain"
        cls.L_SERVICES = f"{cls.BASE}.application.services"
        cls.L_INPUT_PORTS = f"{cls.BASE}.application.input_ports"
        cls.L_OUTPUT_PORTS = f"{cls.BASE}.application.output_ports"
        cls.L_INFRA = f"{cls.BASE}.infrastructure"

    def test_domain_purity(self):
        """
        RULE 1 - Domain Purity:
        Domain entities must not import other internal layers
        (services, ports, infrastructure). The domain is the pure core.
        """
        forbidden_for_domain = [
            self.L_SERVICES,
            self.L_INPUT_PORTS,
            self.L_OUTPUT_PORTS,
            self.L_INFRA,
        ]

        for forbidden in forbidden_for_domain:
            if forbidden in self.all_nodes:
                Rule() \
                    .modules_that().are_sub_modules_of(self.L_DOMAIN) \
                    .should_not() \
                    .import_modules_that().are_sub_modules_of(forbidden) \
                    .assert_applies(self.evaluable)

    def test_core_isolation_from_infrastructure(self):
        """
        RULE 2 - Core Application Isolation:
        The Application layer (domain, ports, services) must NEVER import
        from the Infrastructure layer.
        """
        if self.L_INFRA in self.all_nodes:
            Rule() \
                .modules_that().are_sub_modules_of(self.L_APP) \
                .should_not() \
                .import_modules_that().are_sub_modules_of(self.L_INFRA) \
                .assert_applies(self.evaluable)

    def test_no_technical_frameworks_in_core(self):
        """
        RULE 3 - Technical Framework Isolation:
        No module in the Application layer should import technical frameworks
        like Flask, SQLAlchemy, or Pydantic.
        """
        technical_frameworks = ("flask", "sqlalchemy", "pydantic")
        forbidden_prefixes = tuple(f"{fw}." for fw in technical_frameworks)

        violations = [
            f"{source} -> {target}"
            for source, target in self.evaluable._graph.edges
            if self.L_APP in str(source)
            and (
                str(target).lower() in technical_frameworks
                or str(target).lower().startswith(forbidden_prefixes)
            )
        ]

        assert not violations, (
            "Architecture Violation: Application layer imports forbidden frameworks:\n"
            + "\n".join(violations)
        )

    def test_infrastructure_depends_on_application(self):
        """
        RULE 4 - Inward Dependencies:
        Infrastructure must depend on Application (and not the other way around).
        At least one adapter must import a port or domain entity.
        """
        infra_to_app_exists = any(
            self.L_INFRA in str(source) and self.L_APP in str(target)
            for source, target in self.evaluable._graph.edges
        )

        assert infra_to_app_exists, (
            f"Architecture Violation: No dependency found from Infrastructure to Application "
            f"(Prefix used: {self.BASE})"
        )

    def test_infrastructure_does_not_import_services(self):
        """
        RULE 5 - Infrastructure Isolation :
        Infrastructure must only depend on Ports (interfaces) or Domain.
        It must never depend directly on Services (implementations).
        """
        if self.L_INFRA in self.all_nodes and self.L_SERVICES in self.all_nodes:
            Rule() \
                .modules_that().are_sub_modules_of(self.L_INFRA) \
                .should_not() \
                .import_modules_that().are_sub_modules_of(self.L_SERVICES) \
                .assert_applies(self.evaluable)

    def test_ports_do_not_import_services(self):
        """
        RULE 6 - Port Independence:
        Ports (input and output) define the contracts. They must not
        depend on the Services implementing them.
        """
        if self.L_SERVICES in self.all_nodes:
            for port_module in [self.L_INPUT_PORTS, self.L_OUTPUT_PORTS]:
                if port_module in self.all_nodes:
                    Rule() \
                        .modules_that().are_sub_modules_of(port_module) \
                        .should_not() \
                        .import_modules_that().are_sub_modules_of(self.L_SERVICES) \
                        .assert_applies(self.evaluable)
