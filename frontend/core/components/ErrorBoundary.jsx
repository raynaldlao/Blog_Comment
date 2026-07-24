import React from 'react';
import { _ } from '../utils/i18n';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="alert alert-error">
          {_('Something went wrong. Please reload the page.')}
        </div>
      );
    }
    return this.props.children;
  }
}