import { useState } from 'react';
import axios from 'axios';
import { apiUrl } from '../config';
import UploadCard from '../components/UploadCard';
import ResultDisplay from '../components/ResultDisplay';
import GradCamViewer from '../components/GradCamViewer';
import { Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Home() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const resetScan = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setLoading(false);
  };

  const handleFileChange = (nextFile) => {
    setFile(nextFile);
    // New selection or clear — drop prior scan so the UI never references a missing file
    setResult(null);
    setError(null);
    setLoading(false);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(apiUrl('/predict'), formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      // Prefer the backend's 503 OOM message when present; otherwise keep generic fallback
      if (status === 503 && typeof detail === 'string') {
        setError(detail);
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError("An error occurred during analysis.");
      }
    } finally {
      setLoading(false);
    }
  };

  const isVideo = Boolean(file?.type?.startsWith('video/'));

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-accent to-blue-400">
          AI Deepfake Detection
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Upload an image or video to verify its authenticity. Our Hybrid CNN + Transformer model analyzes visual artifacts to detect manipulation.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <UploadCard file={file} setFile={handleFileChange} onClear={resetScan} />
          
          <button
            onClick={handleAnalyze}
            disabled={!file || loading}
            className="w-full py-4 rounded-xl font-bold text-white bg-accent hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-[0_0_20px_rgba(124,58,237,0.3)] hover:shadow-[0_0_30px_rgba(124,58,237,0.5)] flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing Media...
              </>
            ) : (
              "Analyze Media"
            )}
          </button>

          {error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </motion.div>
          )}
        </div>

        <div className="space-y-6">
          {!result && !loading && (
            <div className="h-full min-h-[300px] border border-gray-800 rounded-2xl flex items-center justify-center bg-gray-900/30">
              <p className="text-gray-500">Results will appear here</p>
            </div>
          )}
          
          {loading && (
            <div className="h-full min-h-[300px] border border-gray-800 rounded-2xl flex flex-col items-center justify-center bg-gray-900/30 space-y-4">
               <Loader2 className="w-10 h-10 text-accent animate-spin" />
               <p className="text-gray-400 animate-pulse">Running inference...</p>
            </div>
          )}

          {result && file && !loading && (
            <div className="space-y-6">
              <ResultDisplay result={result} />
              
              {!isVideo && result.grad_cam_image && (
                <GradCamViewer originalFile={file} gradCamBase64={result.grad_cam_image} />
              )}

              {isVideo && result.frame_results && (
                <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                   <h4 className="text-sm font-semibold text-gray-300 mb-3">Frame Timeline (1 fps)</h4>
                   <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
                     {result.frame_results.map(f => (
                       <div key={f.frame_num} className="flex-shrink-0 bg-gray-900 p-2 rounded-lg text-center min-w-[80px]">
                         <p className="text-xs text-gray-400 mb-1">Sec {f.frame_num}</p>
                         <span className={`text-xs font-bold ${f.label === 'Fake' ? 'text-red-500' : 'text-green-500'}`}>
                           {f.label}
                         </span>
                         <p className="text-[10px] text-gray-500 mt-1">{(f.confidence * 100).toFixed(0)}%</p>
                       </div>
                     ))}
                   </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
