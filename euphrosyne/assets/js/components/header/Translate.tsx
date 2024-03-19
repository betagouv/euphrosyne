import { useState, useEffect } from "react";
export default function Translate() {
  const t = {
    "Select a language": window.gettext("Select a language"),
  };

  const locales: [string, string][] = [
    ["fr", "FR - Français"],
    ["en", "EN - English"],
  ];
  const [currentLang, setCurrentLang] = useState("fr");
  const currentLangLabel = (locales.find(
    (locale) => locale[0] === currentLang
  ) || locales[0])[1];

  const changeLang = (lang: string) => {
    if (currentLang === lang) return;
    // Replace or set django_language cookie and currentLang then reload page
    document.cookie = `django_language=${lang}; path=/`;
    setCurrentLang(lang);
    window.location.reload();
  };

  useEffect(() => {
    // Find current lang in django_language cookie
    setCurrentLang(
      document.cookie
        .split("; ")
        .find((row) => row.startsWith("django_language="))
        ?.split("=")[1] || "fr"
    );
  }, []);

  return (
    <nav role="navigation" className="fr-translate fr-nav">
      <div className="fr-nav__item">
        <button
          className="fr-translate__btn fr-btn fr-btn--tertiary"
          aria-controls="translate-collaspse"
          aria-expanded="false"
          title={t["Select a language"]}
        >
          {currentLangLabel.split("-")[0]}
          <span className="fr-hidden-lg">
            - {currentLangLabel.split("-")[1]}
          </span>
        </button>
        <div
          className="fr-collapse fr-translate__menu fr-menu"
          id="translate-collaspse"
        >
          <ul className="fr-menu__list">
            {locales.map((locale) => (
              <li key={locale[0]}>
                <a
                  className="fr-translate__language fr-nav__link"
                  hrefLang={locale[0]}
                  lang={locale[0]}
                  href="#"
                  aria-current={locale[0] === currentLang ? "true" : undefined}
                  onClick={(e) => {
                    e.preventDefault();
                    changeLang(locale[0]);
                  }}
                >
                  {locale[1]}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </nav>
  );
}
