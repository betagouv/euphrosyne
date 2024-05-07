import { NavItem } from "../../INav";

interface HeaderNavProps {
  currentPath: string;
  items: NavItem[];
}

type AriaCurrent = "page" | "false";

const isCurrentPath = (currentPath: string, navItem: NavItem): boolean => {
  if (!currentPath) {
    return false;
  }

  if (navItem.item) {
    if (navItem.item.exactPath) {
      return navItem.item.href == currentPath;
    }

    return (
      currentPath.includes(navItem.item.href) ||
      navItem.item.extraPath?.some((path) => currentPath.includes(path)) ||
      false
    );
  } else {
    return (
      navItem.items?.some((item) => isCurrentPath(currentPath, item)) || false
    );
  }
};

function NavigationLink({
  href,
  ariaCurrent,
  title,
  iconName,
  badge,
}: {
  href: string;
  ariaCurrent: AriaCurrent;
  title: string;
  iconName?: string;
  badge?: number;
}) {
  return (
    <a
      className={`fr-nav__link fr-link--icon-left ${iconName}`}
      href={href}
      target="_self"
      aria-current={ariaCurrent}
    >
      {title}
      {!!badge && (
        <span className="fr-badge fr-badge--new fr-badge--no-icon fr-badge--sm fr-ml-1v">
          {badge}
        </span>
      )}
    </a>
  );
}

function HeaderMenu({
  items,
  label,
  ariaCurrent,
}: {
  items: NavItem[];
  label: string;
  ariaCurrent?: AriaCurrent;
}) {
  return (
    <>
      <button
        className="fr-nav__btn"
        aria-expanded="false"
        aria-controls={`menu-${label}`}
        aria-current={ariaCurrent}
      >
        {label}
      </button>
      <div className="fr-collapse fr-menu" id={`menu-${label}`}>
        <ul className="fr-menu__list">
          {items.map(
            (item) =>
              item.item && (
                <li
                  className="fr-menu__item"
                  key={`menu-${item.item?.href}-${item.title}`}
                >
                  <NavigationLink
                    href={item.item.href}
                    ariaCurrent="false"
                    title={item.title}
                    iconName={item.item?.iconName}
                  />
                </li>
              ),
          )}
        </ul>
      </div>
    </>
  );
}

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
            {items.map((item, index) => (
              <li className="fr-nav__item" key={`nav-${index}-${item.title}`}>
                {item.items ? (
                  <HeaderMenu
                    items={item.items}
                    label={item.title}
                    ariaCurrent={
                      isCurrentPath(currentPath, item) ? "page" : "false"
                    }
                  />
                ) : (
                  item.item && (
                    <NavigationLink
                      href={item.item.href}
                      ariaCurrent={
                        isCurrentPath(currentPath, item) ? "page" : "false"
                      }
                      title={item.title}
                      iconName={item.item.iconName}
                      badge={item.item.badge}
                    />
                  )
                )}
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </div>
  );
}
