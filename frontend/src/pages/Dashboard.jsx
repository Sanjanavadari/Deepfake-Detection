import { useState, useEffect } from 'react';
import axios from 'axios';
import { apiUrl } from '../config';
import { getApiErrorMessage } from '../utils/apiErrors';
import { Activity, AlertTriangle, Info } from 'lucide-react';
import HistoryTable from '../components/HistoryTable';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [metricsError, setMetricsError] = useState(null);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const res = await axios.get(apiUrl('/evaluate'));
      setMetrics(res.data);
      setMetricsError(null);
    } catch (err) {
      setMetricsError(
        getApiErrorMessage(err, 'Failed to load metrics. The model may not be trained yet.')
      );
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Model Dashboard</h1>
        <p className="text-gray-400">Monitor performance metrics and review prediction history.</p>
      </div>

      {/* Metrics Section */}
      <div className="bg-gray-800/30 rounded-2xl p-6 border border-gray-700/50">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
          <Activity className="text-accent w-5 h-5" />
          Evaluation Metrics
        </h2>
        
        {metricsError ? (
          <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5" />
            <p>{metricsError}</p>
          </div>
        ) : metrics ? (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <MetricCard label="Accuracy" value={`${(metrics.accuracy * 100).toFixed(1)}%`} />
            <MetricCard label="F1-Score" value={metrics.f1_score.toFixed(3)} />
            <MetricCard label="AUC-ROC" value={metrics.auc_roc.toFixed(3)} />
            <MetricCard label="Precision" value={metrics.precision.toFixed(3)} />
            <MetricCard label="Recall" value={metrics.recall.toFixed(3)} />
          </div>
        ) : (
          <div className="animate-pulse flex gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-24 flex-1 bg-gray-700/50 rounded-xl"></div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Training — local-only notice (replaces interactive Training Configuration) */}
        <div className="lg:col-span-1 bg-gray-800/30 rounded-2xl border border-gray-700/50 p-6 flex flex-col">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Info className="text-accent w-5 h-5" />
            Model Training
          </h2>
          <div className="flex-1 rounded-xl bg-gray-900/60 border border-gray-700/60 p-5 space-y-3">
            <p className="text-sm font-medium text-gray-200">
              Training is available in local development only.
            </p>
            <p className="text-sm text-gray-400 leading-relaxed">
              Retraining requires the <code className="text-gray-300 bg-gray-800 px-1.5 py-0.5 rounded text-xs">real/</code> and{' '}
              <code className="text-gray-300 bg-gray-800 px-1.5 py-0.5 rounded text-xs">fake/</code> dataset
              folders on disk. Those folders are not present in this deployed environment, so training
              cannot be started from the hosted Dashboard.
            </p>
            <p className="text-sm text-gray-400 leading-relaxed">
              To retrain, run the backend locally with the dataset available, then deploy the updated{' '}
              <code className="text-gray-300 bg-gray-800 px-1.5 py-0.5 rounded text-xs">best_model.pth</code> weights.
            </p>
          </div>
        </div>

        {/* History Table */}
        <div className="lg:col-span-2">
          <HistoryTable />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-700 text-center">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
