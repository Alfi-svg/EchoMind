import React, { useState } from 'react';

const Home = ({ onSuccess }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null); // error should store a STRING

  const handleSubmit = async (e) => {
    e.preventDefault(); 
    setError(null);
    setIsAnalyzing(true);

    const form = e.target;
    const formData = new FormData(form);

    try {
      const response = await fetch('http://127.0.0.1:8000/run', {
        method: 'POST',
        body: formData,
      });

      // Check if the response is actually JSON before parsing
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        // This handles the "<!doctype..." error gracefully
        const text = await response.text();
        console.error("Backend sent HTML instead of JSON:", text.substring(0, 100)); // Log first 100 chars
        throw new Error("Backend returned HTML (HTML Page) instead of JSON Data. Did you update routes/web.py?");
      }

      if (!response.ok) {
        throw new Error(`Server Error: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      
      if (onSuccess) {
        onSuccess(result);
      }

    } catch (err) {
      console.error("Analysis Failed:", err);
      // ✅ FIX: Ensure we store a String, not the Error Object
      setError(err.message || "An unexpected error occurred");
      setIsAnalyzing(false); 
    }
  };

  if (isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-center animate-fade-in">
        <div className="relative w-20 h-20 mb-6">
            <div className="absolute inset-0 border-4 border-[#7c5cff]/30 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-[#7c5cff] border-t-transparent rounded-full animate-spin"></div>
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Analyzing Video...</h2>
        <p className="text-muted mt-2 text-sm">Processing social context & visual features</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="glass-card rounded-2xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Analysis Dashboard</h1>
          <p className="text-muted text-sm">Upload content to generate explainable AI insights</p>
        </div>

        {/* ✅ FIX: Error display is now safe because 'error' is forced to be a string above */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-200 text-sm flex flex-col items-center gap-1 text-center">
            <div className="flex items-center gap-2 font-bold">
               <span className="w-2 h-2 rounded-full bg-red-500"></span>
               Analysis Failed
            </div>
            <span className="opacity-90">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                Upload Video
              </label>
              <input 
                type="file" 
                name="video_file" 
                accept="video/*" 
                className="input-field file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#7c5cff]/10 file:text-[#7c5cff] hover:file:bg-[#7c5cff]/20" 
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                Video URL
              </label>
              <input 
                type="text" 
                name="video_url" 
                placeholder="https://youtube.com/..." 
                className="input-field" 
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
              Optional Context Hint
            </label>
            <input 
              type="text" 
              name="text_hint" 
              placeholder="e.g. বাংলা / English context / Formal setting" 
              className="input-field" 
            />
          </div>

          <button type="submit" className="btn-primary">
            Run Analysis
          </button>
        </form>
      </div>
    </div>
  );
};

export default Home;