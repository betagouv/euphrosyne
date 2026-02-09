import * as Sentry from "@sentry/browser";
import { jwtFetch } from "../../../shared/js/jwt";

interface IFeedbackAttachment {
  contentType: string;
  data: Uint8Array;
  filename: string;
}

interface IFeedbackForm {
  email: string;
  message: string;
  name: string;
  attachments?: IFeedbackAttachment[];
}

function sendFeedback(feedback: IFeedbackForm) {
  const formData = new FormData();
  formData.append("email", feedback.email);
  formData.append("message", feedback.message);
  formData.append("name", feedback.name);

  if (feedback.attachments) {
    feedback.attachments.forEach((attachment) => {
      const file = new File(
        [attachment.data.buffer as ArrayBuffer],
        attachment.filename,
        {
          type: attachment.contentType,
        },
      );
      formData.append(`attachments`, file);
    });
  }

  jwtFetch(
    "/api/feedback/",
    {
      method: "POST",
      body: formData,
    },
    null,
  );
}

Sentry.init({
  dsn: process.env.SENTRY_DSN_FRONTEND,
  environment: process.env.SENTRY_ENVIRONMENT,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
    Sentry.feedbackIntegration({
      triggerLabel: window.gettext("Need help?"),
      formTitle: window.gettext("Send us a message"),
      nameLabel: window.gettext("Name"),
      namePlaceholder: window.gettext("Full name"),
      emailLabel: window.gettext("Email"),
      emailPlaceholder: window.gettext("Email"),
      messageLabel: window.gettext("Message"),
      isRequiredLabel: window.gettext("(Required)"),
      messagePlaceholder: window.gettext("Type your message here"),
      addScreenshotButtonLabel: window.gettext("Add Screenshot"),
      removeScreenshotButtonLabel: window.gettext("Remove Screenshot"),
      submitButtonLabel: window.gettext("Send message"),
      cancelButtonLabel: window.gettext("Cancel"),

      // Send feedback manually has we don't have access to feedback on beta gouv sentry instance.
      onSubmitSuccess: (data: IFeedbackForm) => {
        sendFeedback(data);
      },
    }),
  ],
  tracesSampleRate: 0.1,
});
