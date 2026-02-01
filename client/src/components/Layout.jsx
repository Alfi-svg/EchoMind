import React from 'react';

const Header = () => (
  <header className="fixed top-0 left-0 w-full h-16 bg-[#0b1020]/80 backdrop-blur-md border-b border-white/10 z-40 flex items-center justify-between px-6">
    <div className="text-2xl font-bold text-accent">EchoMind</div>
    <div className="hidden sm:block text-sm font-medium text-muted">Explainable AI</div>
  </header>
);

const Footer = () => (
  <footer className="fixed bottom-0 left-0 w-full h-10 bg-[#0b1020]/90 backdrop-blur-md border-t border-white/10 z-40 flex items-center justify-center text-xs font-semibold text-muted/60">
    Developed by: TeamEcho
  </footer>
);

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col pt-24 pb-20 px-4">
      <Header />
      <main className="flex-1 w-full max-w-4xl mx-auto animate-fade-in">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;