export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center space-y-8">
        {/* Logo */}
        <div className="flex items-center justify-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/25">
            <svg
              className="w-10 h-10 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            NEURAXIS
          </h1>
        </div>

        {/* Tagline */}
        <p className="text-xl text-slate-600 dark:text-slate-300 max-w-lg">
          AI-Powered Medical Diagnosis Platform
        </p>

        {/* Status Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 font-medium">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Development Server Running
        </div>

        {/* Quick Links */}
        <div className="flex gap-4 justify-center flex-wrap">
          <a
            href="/dashboard"
            className="px-6 py-3 rounded-xl bg-primary-600 text-white font-semibold hover:bg-primary-700 transition-colors shadow-lg shadow-primary-500/25"
          >
            Go to Dashboard
          </a>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-semibold hover:border-primary-500 hover:text-primary-600 transition-colors"
          >
            API Documentation
          </a>
        </div>

        {/* Tech Stack */}
        <div className="pt-8 border-t border-slate-200 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            Built with
          </p>
          <div className="flex gap-6 justify-center text-slate-400 dark:text-slate-500">
            <span className="flex items-center gap-2">
              <span className="font-semibold">Next.js 15</span>
            </span>
            <span className="flex items-center gap-2">
              <span className="font-semibold">FastAPI</span>
            </span>
            <span className="flex items-center gap-2">
              <span className="font-semibold">Turborepo</span>
            </span>
          </div>
        </div>
      </div>
    </main>
  );
}
