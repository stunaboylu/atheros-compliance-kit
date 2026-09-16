// Extends app.json. The only thing added is the web base URL, and it is read
// from the environment because the same export is served from two places:
// `/demo` on a local preview and `/compliance-kit/demo` on atherosai.com.
// Hard-coding either would make the other one 404 on every script — and on
// every `router.push`, since the router prefixes its paths with this value too.
//
// scripts/build_public.py sets CONSOLE_BASE_URL. Unset means `/`, which is
// what `npm run web` wants.
module.exports = ({ config }) => ({
  ...config,
  experiments: {
    ...config.experiments,
    baseUrl: process.env.CONSOLE_BASE_URL || undefined,
  },
});
