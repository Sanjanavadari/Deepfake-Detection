import { useState, useEffect } from 'react';
import axios from 'axios';
import { apiUrl } from '../config';
import { getApiErrorMessage } from '../utils/apiErrors';
import { Clock, ChevronLeft, ChevronRight, CheckCircle, XCircle, Image as ImageIcon, AlertTriangle } from 'lucide-react';

const SKELETON_ROWS = 5;

export default function HistoryTable() {
  const [history, setHistory] = useState([]);
  const [historyError, setHistoryError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const rowsPerPage = 10;

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    setHistoryError(null);
    try {
      const res = await axios.get(apiUrl('/history'));
      setHistory(res.data);
    } catch (err) {
      setHistory([]);
      setHistoryError(getApiErrorMessage(err, 'Failed to load prediction history.'));
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(history.length / rowsPerPage);
  const paginatedData = history.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  return (
    <div className="bg-gray-800/50 rounded-2xl border border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-700 flex items-center gap-2">
        <Clock className="w-5 h-5 text-accent" />
        <h3 className="text-lg font-semibold text-white">Prediction History</h3>
      </div>
      
      <div className="overflow-x-auto">
        {historyError ? (
          <div className="px-6 py-10 flex flex-col items-center text-center gap-3">
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-yellow-500">{historyError}</p>
              <p className="text-xs text-gray-500">Prediction history couldn't be loaded.</p>
            </div>
            <button
              onClick={fetchHistory}
              className="mt-1 px-3 py-1.5 rounded-lg bg-accent hover:bg-violet-500 text-white text-xs font-medium transition-colors"
            >
              Retry
            </button>
          </div>
        ) : (
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="bg-gray-900/50 text-xs uppercase text-gray-400">
            <tr>
              <th className="px-6 py-4 font-medium">Filename</th>
              <th className="px-6 py-4 font-medium">Label</th>
              <th className="px-6 py-4 font-medium">Confidence</th>
              <th className="px-6 py-4 font-medium">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/50">
            {loading ? (
              [...Array(SKELETON_ROWS)].map((_, i) => (
                <tr key={i}>
                  <td className="px-6 py-3"><div className="h-4 bg-gray-700/50 rounded animate-pulse w-32"></div></td>
                  <td className="px-6 py-3"><div className="h-4 bg-gray-700/50 rounded animate-pulse w-20"></div></td>
                  <td className="px-6 py-3"><div className="h-4 bg-gray-700/50 rounded animate-pulse w-12"></div></td>
                  <td className="px-6 py-3"><div className="h-4 bg-gray-700/50 rounded animate-pulse w-24"></div></td>
                </tr>
              ))
            ) : paginatedData.length === 0 ? (
              <tr>
                <td colSpan="4" className="px-6 py-10">
                  <div className="flex flex-col items-center text-center gap-2">
                    <ImageIcon className="w-8 h-8 text-gray-600" />
                    <p className="text-gray-500 font-medium">No predictions yet</p>
                    <p className="text-xs text-gray-600">Analyze an image or video to see results here</p>
                  </div>
                </td>
              </tr>
            ) : (
              paginatedData.map((row) => {
                const isFake = row.label === "Fake";
                return (
                  <tr key={row.id} className="hover:bg-gray-700/30 transition-colors">
                    <td className="px-6 py-3 font-medium text-white truncate max-w-[200px]">{row.filename}</td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium ${isFake ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-green-500/10 text-green-500 border border-green-500/20'}`}>
                        {isFake ? <XCircle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                        {row.label}
                      </span>
                    </td>
                    <td className="px-6 py-3">{(row.confidence * 100).toFixed(2)}%</td>
                    <td className="px-6 py-3 text-gray-400">{new Date(row.timestamp).toLocaleString()}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
        )}
      </div>

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="p-4 border-t border-gray-700 flex items-center justify-between">
          <span className="text-sm text-gray-400">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button 
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded bg-gray-700 text-white disabled:opacity-50 hover:bg-gray-600 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded bg-gray-700 text-white disabled:opacity-50 hover:bg-gray-600 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
