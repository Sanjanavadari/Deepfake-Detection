import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { Activity, Play, Terminal, Target, AlertTriangle } from 'lucide-react';
import HistoryTable from '../components/HistoryTable';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [metricsError, setMetricsError] = useState(null);
  
  // Training State
  const [epochs, setEpochs] = useState(5);
  const [batchSize, setBatchSize] = useState(16);
  const [learningRate, setLearningRate] = useState(0.001);
  const [isTraining, setIsTraining] = useState(false);
  const [logs, setLogs] = useState([]);
  
  const logEndRef = useRef(null);

  useEffect(() => {
    fetchMetrics();
  }, []);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const fetchMetrics = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/evaluate`);
      setMetrics(res.data);
      setMetricsError(null);
    } catch (err) {
      setMetricsError(err.response?.data?.detail || "Failed to load metrics. The model may not be trained yet.");
    }
  };

  const startTraining = () => {
    if (isTraining) return;
    setIsTraining(true);
    setLogs([{ type: 'info', msg: 'Starting training job...' }]);

    fetch(`${API_BASE_URL}/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ epochs, batch_size: batchSize, learning_rate: learningRate })
    })
    .then(response => {
      if (!response.ok) {
        setLogs(prev => [...prev, {
          type: 'error',
          msg: `Failed to start training: server returned HTTP ${response.status}`,
        }]);
        setIsTraining(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      const processStream = async () => {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n\n');
          
          for (let line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '');
              try {
                const data = JSON.parse(dataStr);
                
                if (data.error) {
                  const isDeployedMessage = data.error.includes('not available in this deployed environment');
                  setLogs(prev => [...prev, {
                    type: isDeployedMessage ? 'warning' : 'error',
                    msg: isDeployedMessage ? data.error : `Error: ${data.error}`,
                  }]);
                  setIsTraining(false);
                  return;
                } else if (data.message) {
                  setLogs(prev => [...prev, { type: 'info', msg: data.message }]);
                } else {
                  setLogs(prev => [...prev, { 
                    type: 'log', 
                    msg: `Epoch [${data.epoch}/${epochs}] - Train Loss: ${data.train_loss.toFixed(4)} | Val Loss: ${data.val_loss.toFixed(4)} | Val Acc: ${(data.val_acc*100).toFixed(1)}%` 
                  }]);
                }
              } catch (e) {
                // Ignore parse errors for partial chunks
              }
            }
          }
        }
        setIsTraining(false);
        setLogs(prev => [...prev, { type: 'success', msg: 'Training stream closed.' }]);
        fetchMetrics(); // Refresh metrics after training
      };

      processStream().catch(err => {
        setLogs(prev => [...prev, { type: 'error', msg: `Stream error: ${err.message}` }]);
        setIsTraining(false);
      });
    })
    .catch(err => {
      setLogs(prev => [...prev, { type: 'error', msg: `Failed to start training: ${err.message}` }]);
      setIsTraining(false);
    });
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Model Dashboard</h1>
        <p className="text-gray-400">Monitor performance metrics and retrain the Hybrid CNN + Transformer.</p>
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
        {/* Training Panel */}
        <div className="lg:col-span-1 bg-gray-800/30 rounded-2xl border border-gray-700/50 flex flex-col">
          <div className="p-6 border-b border-gray-700/50">
            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
              <Target className="text-accent w-5 h-5" />
              Training Configuration
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Epochs</label>
                <input 
                  type="number" 
                  value={epochs} 
                  onChange={(e) => setEpochs(Number(e.target.value))}
                  disabled={isTraining}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-accent disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Batch Size</label>
                <input 
                  type="number" 
                  value={batchSize} 
                  onChange={(e) => setBatchSize(Number(e.target.value))}
                  disabled={isTraining}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-accent disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Learning Rate</label>
                <input 
                  type="number" 
                  step="0.0001"
                  value={learningRate} 
                  onChange={(e) => setLearningRate(Number(e.target.value))}
                  disabled={isTraining}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-accent disabled:opacity-50"
                />
              </div>
            </div>
            <button
              onClick={startTraining}
              disabled={isTraining}
              className="mt-6 w-full py-3 rounded-xl font-bold text-white bg-accent hover:bg-violet-500 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
            >
              {isTraining ? (
                <>
                  <Terminal className="w-5 h-5 animate-pulse" /> Training in Progress...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" /> Start Training
                </>
              )}
            </button>
          </div>
          
          {/* Console Output */}
          <div className="flex-1 p-6 bg-black rounded-b-2xl overflow-hidden flex flex-col max-h-[300px]">
            <h3 className="text-xs font-mono text-gray-500 mb-2 uppercase tracking-wider">Live Logs</h3>
            <div className="flex-1 overflow-y-auto font-mono text-sm space-y-1 custom-scrollbar pr-2">
              {logs.length === 0 ? (
                <p className="text-gray-600 italic">No logs yet.</p>
              ) : (
                logs.map((l, i) => (
                  <p key={i} className={`
                    ${l.type === 'error' ? 'text-red-400' : ''}
                    ${l.type === 'warning' ? 'text-yellow-400' : ''}
                    ${l.type === 'success' ? 'text-green-400' : ''}
                    ${l.type === 'info' ? 'text-blue-400' : ''}
                    ${l.type === 'log' ? 'text-gray-300' : ''}
                  `}>
                    <span className="text-gray-600 mr-2">{'>'}</span>{l.msg}
                  </p>
                ))
              )}
              <div ref={logEndRef} />
            </div>
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
