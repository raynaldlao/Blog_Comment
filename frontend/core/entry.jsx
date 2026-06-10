import React from 'react';
import ReactDOM from 'react-dom/client';
import '@blocknote/mantine/style.css';
import '@blocknote/core/fonts/inter.css';
import ArticleEditor from './ArticleEditor';
import ArticleViewer from './ArticleViewer';

const root = document.getElementById('root');
const page = root?.dataset.page;

let Component;
if (page === 'create' || page === 'edit') {
  Component = ArticleEditor;
} else if (page === 'view') {
  Component = ArticleViewer;
}

if (root && Component) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <Component />
    </React.StrictMode>,
  );
}
