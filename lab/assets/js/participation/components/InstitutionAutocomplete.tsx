import React, { useState, useEffect, useRef, useCallback } from "react";
import { Institution } from "../types";

export interface RorResult {
  id: string;
  names: {
    lang: string;
    types: string[];
    value: string;
  }[];
  locations: {
    geonames_details: {
      country_name: string;
    };
  }[];
}

export interface TypeAheadResult {
  label: string;
  id: string;
  name: string;
  country: string;
}

interface InstitutionAutocompleteProps {
  name: string;
  id?: string;
  value: Institution;
  onChange: (institution: Institution | null) => void;
}

export default function InstitutionAutocomplete({
  id,
  value,
  onChange,
  ...props
}: InstitutionAutocompleteProps &
  Omit<React.HTMLAttributes<HTMLDivElement>, "onChange">) {
  const [results, setResults] = useState<TypeAheadResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState(false);

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const t = {
    institution: window.gettext("Institution"),
    country: window.gettext("Country"),
    noResults: window.gettext(
      "No results found. You can register a new institution using",
    ),
    thisForm: window.gettext("this form"),
    errorMessage: window.gettext("An error occurred while fetching results"),
  };

  // Handle clicks outside to close the dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setShowResults(false);
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, []);

  // Fetch results from ROR API
  const fetchResults = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      setShowResults(false);
      return;
    }

    setError(false);

    try {
      const response = await fetch(
        "https://api.ror.org/organizations?query=" + encodeURIComponent(query),
      );

      if (!response.ok) {
        throw new Error("Failed to fetch results");
      }

      const data = await response.json();
      const mappedResults: TypeAheadResult[] = data.items.map(
        (item: RorResult) => ({
          label: `${item.names[0].value}, ${item.locations[0].geonames_details.country_name}`,
          id: item.id,
          name: item.names[0].value,
          country: item.locations[0].geonames_details.country_name,
        }),
      );

      setResults(mappedResults);
      setShowResults(true);
    } catch (err) {
      console.error(err);
      setError(true);
      setShowResults(true);
    }
  }, []);

  // Handle input changes with debounce
  const handleNameInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;

    onChange({
      ...value,
      name: newValue,
      id: null,
      rorId: null,
    });

    // Debounce the API call
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      fetchResults(newValue);
    }, 500);
  };

  const handleCountryInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({
      ...value,
      country: e.target.value,
      id: null,
      rorId: null,
    });
  };

  // Handle result selection
  const handleResultClick = (result: TypeAheadResult) => {
    setShowResults(false);

    const institution: Institution = {
      id: null,
      name: result.name,
      country: result.country,
      rorId: result.id,
    };

    onChange(institution);
  };

  return (
    <div
      className={`autocomplete-input flex-container ${props.className}`}
      ref={containerRef}
    >
      <div className="typeahead-field fr-mr-1w fr-input-wrap fr-icon-search-line">
        <input
          value={value.name}
          onChange={handleNameInput}
          className="fr-input autocomplete-input__name"
          placeholder={t.institution}
          autoComplete="off"
          type="text"
          id={id}
        />
        {showResults && (
          <div className="typeahead-list">
            {error ? (
              <div>{t.errorMessage}</div>
            ) : results.length === 0 ? (
              <div>
                {t.noResults}{" "}
                <a
                  href="https://docs.google.com/forms/d/e/1FAIpQLSdJYaMTCwS7muuTa-B_CnAtCSkKzt19lkirAKG4u7umH9Nosg/viewform"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t.thisForm}
                </a>
              </div>
            ) : (
              results.map((result) => (
                <button
                  key={result.id}
                  type="button"
                  onClick={() => handleResultClick(result)}
                >
                  {result.label}
                </button>
              ))
            )}
          </div>
        )}
      </div>
      <input
        value={value.country || ""}
        onChange={handleCountryInput}
        className="fr-input autocomplete-input__country"
        placeholder={t.country}
        type="text"
      />

      <input
        type="hidden"
        value={value.id || ""}
        className="fr-input autocomplete-input__id"
      />
      <input
        type="hidden"
        value={value.rorId || ""}
        className="fr-input autocomplete-input__ror_id"
      />
    </div>
  );
}
