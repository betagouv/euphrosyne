import { useEffect, useState } from "react";
import { jwtFetch } from "../../../../lab/assets/js/jwt.js";
import euphrosyneToolsService from "../../../../lab/workplace/assets/js/euphrosyne-tools-service.js";

const deleteVm = (vm: string) => {
  // Vm name starts with euphro-stg-vm, so we need to remove it
  // Quick and dirty solution
  vm = vm.replace(/euphro-(stg|prod)-vm-/, "");
  return euphrosyneToolsService.deleteVM(vm);
};

function DeleteButton({ vmName }: { vmName: string }) {
  const [isLoading, setIsLoading] = useState(false);
  const onClick = async () => {
    setIsLoading(true);
    await deleteVm(vmName);
    setIsLoading(false);
  };
  return (
    <button
      className="fr-btn fr-btn--lg fr-icon-stop-circle-line fr-btn--tertiary-no-outline"
      title="Stop VM"
      onClick={onClick}
      disabled={isLoading}
    ></button>
  );
}

export default function RunningVMTable() {
  const t = {
    "Virtual machine": window.gettext("Virtual machine"),
    "No running virtual machines": window.gettext(
      "No running virtual machines"
    ),
  };

  const [isLoading, setIsLoading] = useState(true);
  const [vms, setVms] = useState([]);

  useEffect(() => {
    jwtFetch(`${process.env.EUPHROSYNE_TOOLS_API_URL}/vms/`, {
      method: "GET",
    })
      .then((response) => response?.json())
      .then((data) => {
        if (data) {
          setVms(data);
          setIsLoading(false);
        }
      });
  }, []);

  return (
    <div className="fr-table">
      <table>
        <thead>
          <tr>
            <th scope="col">{t["Virtual machine"]}</th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr>
              <td colSpan={2}>...</td>
            </tr>
          ) : (
            <>
              {vms.length !== 0 ? (
                vms.map((vm) => (
                  <tr key={vm}>
                    <td>{vm}</td>
                    <td>
                      <DeleteButton vmName={vm} />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={2}>{t["No running virtual machines"]}</td>
                </tr>
              )}
            </>
          )}
        </tbody>
      </table>
    </div>
  );
}
