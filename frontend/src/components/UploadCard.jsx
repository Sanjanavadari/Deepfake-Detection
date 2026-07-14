import { useState, useRef } from 'react';
import { UploadCloud, FileVideo, Image as ImageIcon, X } from 'lucide-react';
import { motion } from 'framer-motion';

export default function UploadCard({ file, setFile, onClear }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const clearFile = (e) => {
    e.stopPropagation();
    if (onClear) {
      onClear();
    } else {
      setFile(null);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div
      className={`relative w-full rounded-2xl border-2 border-dashed p-8 transition-colors cursor-pointer flex flex-col items-center justify-center min-h-[300px]
        ${isDragging ? 'border-accent bg-accent/10' : 'border-gray-700 bg-gray-800/50 hover:border-gray-500 hover:bg-gray-800'}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !file && fileInputRef.current?.click()}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleChange}
        accept="image/*,video/mp4,video/avi"
        className="hidden"
      />

      {!file ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="text-center flex flex-col items-center pointer-events-none">
          <div className="bg-gray-900 p-4 rounded-full mb-4">
            <UploadCloud className="w-10 h-10 text-accent" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-1">Upload Media</h3>
          <p className="text-sm text-gray-400">Drag & drop an image or video, or click to browse</p>
          <p className="text-xs text-gray-500 mt-2">Supports JPG, PNG, MP4, AVI</p>
        </motion.div>
      ) : (
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full relative">
          <button 
            onClick={clearFile}
            className="absolute -top-4 -right-4 bg-red-500 hover:bg-red-600 text-white p-1 rounded-full z-10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
          
          <div className="bg-gray-900 rounded-xl overflow-hidden border border-gray-700 relative group">
            {file.type.startsWith('video/') ? (
              <div className="aspect-video bg-black flex items-center justify-center">
                <FileVideo className="w-16 h-16 text-gray-600" />
              </div>
            ) : (
              <img 
                src={URL.createObjectURL(file)} 
                alt="Preview" 
                className="w-full h-auto max-h-[300px] object-contain bg-black/50"
              />
            )}
            
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4">
              <div className="flex items-center gap-2">
                {file.type.startsWith('video/') ? <FileVideo className="w-4 h-4 text-accent" /> : <ImageIcon className="w-4 h-4 text-accent" />}
                <p className="text-sm font-medium text-white truncate">{file.name}</p>
              </div>
              <p className="text-xs text-gray-400 mt-1">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
