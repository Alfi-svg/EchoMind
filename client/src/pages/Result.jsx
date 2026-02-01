import React, { useEffect, useRef } from 'react';

// --- CHART COMPONENT ---
const ChartCanvas = ({ data, type = 'motion', title }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;

    // Clear & Grid
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = 20 + (H - 40) * (i / 4);
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    // Colors
    const colors = ["#7c5cff", "#22c55e", "#fbbf24", "#ef4444"];
    
    // TYPE: MOTION LINE GRAPH
    if (type === 'motion' && Array.isArray(data) && data.length > 1) {
      const keys = Object.keys(data[0]).filter(k => k !== 'time'); 
      keys.forEach((key, idx) => {
        ctx.beginPath();
        ctx.strokeStyle = colors[idx % colors.length];
        ctx.lineWidth = 2;
        data.forEach((point, i) => {
          const x = (i / (data.length - 1)) * W;
          const val = point[key] || 0;
          const y = H - 20 - (val * (H - 40)); 
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();
      });
    } 
    // TYPE: BAR CHART (Averages or Variability)
    else if (type === 'bar' && typeof data === 'object') {
       const keys = Object.keys(data);
       if(keys.length === 0) return;
       const barW = (W - 20) / keys.length; 
       keys.forEach((key, i) => {
         const val = data[key] || 0;
         const h = val * (H - 40);
         const x = 10 + i * barW + 5;
         const y = H - 20 - h;
         
         ctx.fillStyle = "rgba(124,92,255,0.85)";
         ctx.fillRect(x, y, barW - 10, h);
         
         // Value
         ctx.fillStyle = "#fff";
         ctx.font = "11px sans-serif";
         ctx.fillText(val.toFixed(2), x, y - 6);
         
         // Label (rotated slightly if needed, simplified here)
         ctx.fillStyle = "rgba(255,255,255,0.6)";
         ctx.font = "10px sans-serif";
         const label = key.replace(/_/g, ' ').split(' ')[0]; // short label
         ctx.fillText(label, x, H-5);
       });
    }
  }, [data, type]);

  return (
    <div className="mb-6">
      <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-2">{title}</h3>
      <canvas ref={canvasRef} width={800} height={200} className="w-full h-48 bg-black/20 rounded-lg border border-white/5" />
    </div>
  );
};

// --- MAIN RESULT COMPONENT ---
const Result = ({ resultData, onBack }) => {
  if (!resultData) return <div className="text-center p-10 text-muted">No Data Available</div>;
  const { phase1, phase2 } = resultData;

  // Badge Component helper
  const Badge = ({ children, color = "default" }) => {
    const styles = {
      default: "bg-white/5 border-white/10 text-gray-300",
      red: "bg-red-500/10 border-red-500/30 text-red-200",
      blue: "bg-blue-500/10 border-blue-500/30 text-blue-200",
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${styles[color] || styles.default}`}>
        {children}
      </span>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4 mb-2">
        <button onClick={onBack} className="flex items-center gap-2 text-muted hover:text-white font-bold text-sm transition-colors">
          ← Back
        </button>
        <h1 className="text-2xl font-bold text-white">Analysis Result</h1>
      </div>

      {/* PHASE 1: LINGUISTICS & SOCIAL CONTEXT */}
      <div className="glass-card rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 border-b-2 border-accent inline-block pb-1">
          Phase 1: Linguistics
        </h2>
        
        {/* Basic Stats */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="bg-white/5 px-4 py-2 rounded-lg border border-white/10">
            <span className="block text-[10px] text-muted uppercase tracking-wider">Language</span>
            <span className="text-white font-bold">{phase1?.language}</span>
          </div>
          <div className="bg-white/5 px-4 py-2 rounded-lg border border-white/10">
            <span className="block text-[10px] text-muted uppercase tracking-wider">Sentiment</span>
            <span className="text-white font-bold">{phase1?.sentiment} <span className="text-muted text-xs font-normal">({phase1?.sentiment_score?.toFixed(2)})</span></span>
          </div>
        </div>

        {/* Transcript */}
        <div className="mb-6">
           <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-2">Transcript</h3>
           <div className="bg-black/30 p-4 rounded-xl border border-white/10 text-sm text-gray-300 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto custom-scrollbar">
             {phase1?.transcript}
           </div>
        </div>

        {/* AI Social Context Analysis */}
        <div className="mt-8">
            <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-3 flex items-center gap-2">
              AI Social Analysis
              <div className="h-[1px] flex-1 bg-white/10"></div>
            </h3>

            {/* Badges Row */}
            {phase1.social_context_ok ? (
              <>
                <div className="flex flex-wrap gap-2 mb-4">
                   <Badge>✅ LLM: {phase1.social_context_model}</Badge>
                   
                   {phase1.social_context_flags?.risk_level && (
                     <Badge color={phase1.social_context_flags.risk_level === 'High' ? 'red' : 'default'}>
                       Risk: {phase1.social_context_flags.risk_level}
                     </Badge>
                   )}
                   
                   {phase1.social_context_flags?.tone && (
                     <Badge>Tone: {phase1.social_context_flags.tone}</Badge>
                   )}
                   
                   {phase1.social_context_flags?.has_slang_or_offensive && (
                     <Badge color="red">⚠️ Possible Slang/Offensive</Badge>
                   )}
                </div>

                {/* Example Terms */}
                {phase1.social_context_flags?.example_terms?.length > 0 && (
                  <p className="text-xs text-muted mb-3">
                    <b className="text-gray-400">Example terms:</b> {phase1.social_context_flags.example_terms.join(", ")}
                  </p>
                )}

                {/* Explanation Text */}
                <div className="bg-white/5 p-4 rounded-xl border border-white/10 text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
                  {phase1.social_context_explanation}
                </div>
              </>
            ) : (
              /* Fallback Mode */
              <div className="bg-red-500/5 border border-red-500/20 p-4 rounded-xl">
                 <div className="text-red-300 font-bold text-sm mb-2">⚠️ LLM Social Context Unavailable (Fallback Mode)</div>
                 <p className="text-muted text-xs mb-3">System is using rule-based explanation.</p>
                 {phase1.social_context_warning && <p className="text-[10px] text-red-400 font-mono mb-2">Debug: {phase1.social_context_warning}</p>}
                 <div className="text-sm text-gray-300 whitespace-pre-wrap">
                    {phase1.social_context_explanation}
                 </div>
              </div>
            )}
        </div>
      </div>

      {/* PHASE 2: VISUAL FEATURES */}
      <div className="glass-card rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 border-b-2 border-success inline-block pb-1">
          Phase 2: Visual Features
        </h2>
        
        <ChartCanvas data={phase2?.timeline_data} type="motion" title="Motion Timeline" />
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ChartCanvas data={phase2?.stats?.averages} type="bar" title="Average Intensity (0-1)" />
            <ChartCanvas data={phase2?.stats?.variability} type="bar" title="Variability / Instability" />
        </div>

        {/* Legend */}
        <div className="flex flex-wrap justify-center gap-4 mt-2 text-[10px] text-muted uppercase tracking-wider">
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[#7c5cff]"></div> Openness</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[#22c55e]"></div> Gestures</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[#fbbf24]"></div> Eye Contact</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[#ef4444]"></div> Pacing</span>
        </div>
      </div>
    </div>
  );
};

export default Result;