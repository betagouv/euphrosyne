import { useEffect, useState } from "react";
import ImageLoading from "../../../../../shared/js/images/ImageLoading";
import { getUserData } from "../../../../../euphrosyne/assets/js/main";

interface RadiationProtectionCheckProps {
  userId: number;
}

export default function RadiationProtectionCheck({
  userId,
}: RadiationProtectionCheckProps) {
  const t = {
    missingCertificate: window.gettext(
      "Missing radiation protection certification",
    ),
  };
  const userData = getUserData();
  if (!userData.isLabAdmin) {
    return <></>;
  }

  const [hasCertificate, setHasCertificate] = useState<boolean | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const resp = await fetch(`/api/radiation-protection/user/${userId}`);
      if (resp.status === 404) {
        return setHasCertificate(false);
      }
      if (!resp.ok) {
        console.error(
          `Error fetching radiation protection certificate for user ${userId}`,
        );
        return setHasCertificate(false);
      }
      return setHasCertificate(true);
    };
    fetchData();
  }, [userId]);

  return (
    <>
      {hasCertificate === null && (
        <div style={{ width: "24px", height: "24px" }}>
          <ImageLoading spinningRadius={80} />
        </div>
      )}
      {hasCertificate === false && (
        <>
          <span
            className="fr-icon-warning-line participation-certification-warning"
            aria-hidden="true"
            aria-describedby={`radiation-protection-check-user-${userId}-tooltip`}
            style={{ display: "inline-flex" }}
          ></span>
          <span
            className="fr-tooltip fr-placement"
            id={`radiation-protection-check-user-${userId}-tooltip`}
            role="tooltip"
            aria-hidden="true"
          >
            {t.missingCertificate}
          </span>
        </>
      )}
    </>
  );
}
