import { ScrollViewStyleReset } from 'expo-router/html';
import React from 'react';

/**
 * The HTML shell for every statically exported page.
 *
 * Two things live here that cannot live in React: the webfont link, and the
 * base CSS that stops react-native-web's root from locking the page to the
 * viewport height (which breaks both long documents and printing).
 */
export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />

        {/* Open Sans is Argon's typeface. Preconnected so the first paint does
            not wait on a DNS round trip, and every rule that uses it names a
            full fallback stack so the page is correct before it arrives — and
            stays correct on a network that blocks Google entirely. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap"
        />

        <ScrollViewStyleReset />
        <style dangerouslySetInnerHTML={{ __html: BASE_CSS }} />
      </head>
      <body>{children}</body>
    </html>
  );
}

const BASE_CSS = `
html, body, #root { height: auto; min-height: 100%; overflow: visible; }
body { margin: 0; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
#root { display: flex; flex-direction: column; }
* { scrollbar-width: thin; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: rgba(136,152,170,.35); border-radius: 999px; }
::-webkit-scrollbar-track { background: transparent; }
`;
