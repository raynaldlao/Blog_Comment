import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import '@blocknote/mantine/style.css';
import '@blocknote/core/fonts/inter.css';
import ErrorBoundary from './components/ErrorBoundary';

const ArticleForm = React.lazy(() => import('./components/ArticleForm'));
const ArticleViewer = React.lazy(() => import('./components/ArticleViewer'));

const root = document.getElementById('root');
const page = root?.dataset.page;

const Component = (page === 'create' || page === 'edit')
  ? ArticleForm
  : (page === 'view' ? ArticleViewer : null);

if (root && Component) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <ErrorBoundary>
        <Suspense fallback={<div className="loading">Loading...</div>}>
          <Component />
        </Suspense>
      </ErrorBoundary>
    </React.StrictMode>,
  );
}
