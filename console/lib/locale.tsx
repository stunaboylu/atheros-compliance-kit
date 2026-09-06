import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

import { Key, Locale, t as translate } from './i18n';

const STORAGE_KEY = 'atheros.locale';

function initial(): Locale {
  // A viewer's language choice is a per-viewer convenience, so it lives in their
  // own browser and nowhere else. Wrapped because the accessor itself throws in a
  // private window or where site data is blocked, and a language preference must
  // never be the reason a compliance report fails to render.
  try {
    const stored = globalThis.localStorage?.getItem(STORAGE_KEY);
    if (stored === 'tr' || stored === 'en') return stored;
    const nav = globalThis.navigator?.language ?? '';
    if (nav.toLowerCase().startsWith('tr')) return 'tr';
  } catch {
    /* no stored preference available */
  }
  return 'en';
}

const Ctx = createContext<{
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: Key) => string;
}>({ locale: 'en', setLocale: () => {}, t: (k) => translate(k, 'en') });

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => initial());

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    try {
      globalThis.localStorage?.setItem(STORAGE_KEY, next);
    } catch {
      /* preference is not persisted; the session still switches */
    }
  }, []);

  const value = useMemo(
    () => ({ locale, setLocale, t: (key: Key) => translate(key, locale) }),
    [locale, setLocale],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useLocale = () => useContext(Ctx);
