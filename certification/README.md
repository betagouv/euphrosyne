# Certification App

Certificaton app management : describe how to get certification, notify users at each step of the process, manage results to quiz and so.

## Certifications package

Certification that a user can be earned. Each certification has a name, a description, a type (like a quiz), and a validity period. It also has information about email templates that are used to invite users to complete the certification and to congratulate them when they succeed.

A quiz certification (`QuizCertification`) represents a quiz that's tied to a specific certification. Each quiz has a unique URL and a passing score.
The quiz results (`QuizResult`) let us store the results of a user taking a quiz. It keeps track of who took the quiz, which quiz they took, their score, and whether they passed or not.

## Notifications package

It manages all the necessary information about the notifications that are sent to users about their certifications.

The `CertificationNotification` class also includes several methods for sending notifications.
Each notification is associated with a user and a certification. It has a type (like an invitation or success), a flag indicating whether it has been sent, and a timestamp for when it was created and last modified. It may also be associated with a `QuizResult`, which represents the result of a user taking a quiz.

The notification can be sent via the `send_notification` method or via the Django command located at `certification/management/commands/send_notifications.py`. The command send all the notifications that have `is_sent` flag set to `False`.

## Providers package

This package offers implementation for external services.
For exampe the `tally` package has a hook where Tally post results on submission.

## Radiation protection module

The `radiation_protection module` is a implementation layer that exposes some function related to New AGLAE radiation protection certification.
