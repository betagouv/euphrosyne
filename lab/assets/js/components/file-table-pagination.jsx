import React from "react";

export default function FileTablePagination({ currentPage, setPage, pages }) {
  const visiblePages = [...Array(pages)]
    .map((_, idx) => idx + 1)
    .filter((page) =>
      [currentPage - 1, currentPage, currentPage + 1].includes(page)
    );

  return (
    <nav role="navigation" className="fr-pagination" aria-label="Pagination">
      <ul className="fr-pagination__list">
        <li>
          <a
            className="fr-pagination__link fr-pagination__link--first"
            aria-disabled={currentPage === 1 ? "true" : undefined}
            role="link"
            href="#"
            onClick={() => setPage(1)}
          >
            {window.gettext("First page")}
          </a>
        </li>
        <li>
          <a
            className="fr-pagination__link fr-pagination__link--prev fr-pagination__link--lg-label"
            aria-disabled={currentPage === 1 ? "true" : undefined}
            role="link"
            href="#"
            title={window.gettext("Previous page")}
            onClick={() => setPage(currentPage - 1)}
          ></a>
        </li>
        {visiblePages.map((page) => (
          <li key={page}>
            <a
              className="fr-pagination__link"
              title={window.interpolate(window.gettext("Page %s"), [page])}
              aria-current={currentPage === page ? "page" : undefined}
              onClick={() => setPage(page)}
              role="title"
              href="#"
            >
              {page}
            </a>
          </li>
        ))}

        {!visiblePages.includes(pages) && (
          <>
            <li>
              <a className="fr-pagination__link fr-displayed-lg">…</a>
            </li>

            <li key={pages}>
              <a
                className="fr-pagination__link"
                title={window.interpolate(window.gettext("Page %s"), [pages])}
                onClick={() => setPage(pages)}
                role="title"
                href="#"
              >
                {pages}
              </a>
            </li>
          </>
        )}

        <li>
          <a
            className="fr-pagination__link fr-pagination__link--next fr-pagination__link--lg-label"
            role="link"
            href="#"
            title={window.gettext("Next page")}
            aria-disabled={currentPage === pages ? "true" : undefined}
            onClick={() => setPage(currentPage + 1)}
          ></a>
        </li>
        <li>
          <a
            className="fr-pagination__link fr-pagination__link--last"
            aria-disabled={currentPage === pages ? "true" : undefined}
            onClick={() => setPage(pages)}
            role="title"
            href="#"
          >
            {window.gettext("Last page")}
          </a>
        </li>
      </ul>
    </nav>
  );
}
