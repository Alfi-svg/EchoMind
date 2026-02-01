import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import SplashScreen from './components/SplashScreen';
import Home from './pages/Home';
import Result from './pages/Result';

function App() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    // 1. Check if backend injected data into window
    if (window.resultData) {
      setData(window.resultData);
    }
    // 2. Loading simulation ends
    // (If you want the splash screen to only show on initial load, this logic is fine)
    const timer = setTimeout(() => setLoading(false), 2200);
    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      {loading && <SplashScreen onFinish={() => setLoading(false)} />}
      
      {!loading && (
        <Layout>
          {data ? <Result resultData={data} /> : <Home />}
        </Layout>
      )}
    </>
  );
}

export default App;