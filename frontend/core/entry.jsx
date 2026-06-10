import React from 'react';
import ReactDOM from 'react-dom/client';
import '@blocknote/mantine/style.css';
import '@blocknote/core/fonts/inter.css';
import ArticleForm from './components/ArticleForm';
import ArticleViewer from './components/ArticleViewer';
import ErrorBoundary from './components/ErrorBoundary';

const root = document.getElementById('root');
const page = root?.dataset.page;

const Component = (page === 'create' || page === 'edit')
  ? ArticleForm
  : (page === 'view' ? ArticleViewer : null);

if (root && Component) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <ErrorBoundary>
        <Component />
      </ErrorBoundary>
    </React.StrictMode>,
  );
}
