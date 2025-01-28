import * as Sentry from "@sentry/browser";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
    Sentry.feedbackIntegration({
      triggerLabel: window.gettext("Need help?"),
      // User Feedback configuration options
    }),
  ],
  tracesSampleRate: 0.1,
});
