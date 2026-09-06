import React, { createContext, useContext, useEffect, useState } from 'react';

import { bundledReport, hasRemoteSource, loadReport, LoadResult } from './data';

const Ctx = createContext<{ state: LoadResult; error: string | null; reload: () => void }>({
  state: bundledReport(),
  error: null,
  reload: () => {},
});

export function ReportProvider({ children }: { children: React.ReactNode }) {
  // Seeded synchronously from the bundled fixture so static export renders real
  // content rather than a spinner, and so the first paint carries data.
  const [state, setState] = useState<LoadResult>(() => bundledReport());
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!hasRemoteSource) return;   // the sync value is already final
    let live = true;
    loadReport()
      .then((r) => live && setState(r))
      .catch((e) => live && setError(String(e)));
    return () => {
      live = false;
    };
  }, [nonce]);

  return (
    <Ctx.Provider value={{ state, error, reload: () => setNonce((n) => n + 1) }}>
      {children}
    </Ctx.Provider>
  );
}

export const useReport = () => useContext(Ctx);
