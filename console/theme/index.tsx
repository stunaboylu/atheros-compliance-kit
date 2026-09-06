import React, { createContext, useContext, useMemo, useState } from 'react';
import { useColorScheme } from 'react-native';

import { dark, light, Palette } from './tokens';

type Mode = 'system' | 'light' | 'dark';

const Ctx = createContext<{ c: Palette; mode: Mode; setMode: (m: Mode) => void; isDark: boolean }>({
  c: dark,
  mode: 'system',
  setMode: () => {},
  isDark: true,
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const system = useColorScheme();
  const [mode, setMode] = useState<Mode>('system');
  const isDark = mode === 'system' ? system !== 'light' : mode === 'dark';
  const value = useMemo(
    () => ({ c: (isDark ? dark : light) as Palette, mode, setMode, isDark }),
    [isDark, mode],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);
export * from './tokens';
