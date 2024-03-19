import { NavItem } from "../../INav";

interface HeaderNavProps {
  currentPath: string;
  items: NavItem[];
}

const isCurrentPath = (currentPath: string, navItem: NavItem) => {
  if (!currentPath) {
    return false;
  }

  if (navItem.exactPath) {
    return navItem.href == currentPath;
  }

  return (
    currentPath.includes(navItem.href) ||
    navItem.extraPath?.some((path) => currentPath.includes(path))
  );
};

export default function HeaderNav({ currentPath, items }: HeaderNavProps) {
  const t = {
    Close: window.gettext("Close"),
  };

  return (
    <div
      className="fr-header__menu fr-modal"
      id="header-modal"
      aria-labelledby="header-modal-btn"
    >
      <div className="fr-container">
        <button
          className="fr-btn--close fr-btn"
          title={t["Close"]}
          aria-controls="header-modal"
        >
          {t["Close"]}
        </button>
        <div className="fr-header__menu-links"></div>
        <nav className="fr-nav" role="navigation" aria-label={"Main menu"}>
          <ul className="fr-nav__list">
            {items.map((item) => (
              <li
                className="fr-nav__item"
                key={`nav-${item.href}-${item.title}`}
              >
                <a
                  className={`fr-nav__link fr-link--icon-left ${item.iconName}`}
                  href={item.href}
                  target="_self"
                  aria-current={
                    isCurrentPath(currentPath, item) ? "page" : "false"
                  }
                >
                  {item.title}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </div>
  );
}
