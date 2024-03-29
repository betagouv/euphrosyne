export const template: string = `
<div class="js-inline-admin-formset inline-group overflow-auto" id="object_set-group" data-inline-type="tabular">
    <table>
        <tbody>
            <tr class="form-row has_original dynamic-object_set" id="object_set-0">
                <td class="field-inventory">
                    <input type="text" name="object_set-0-inventory" class="vTextField" maxlength="255"
                        id="id_object_set-0-inventory">
                </td>
                <td class="field-collection">
                    <input type="text" name="object_set-0-collection" class="vTextField" maxlength="255" disabled=""
                        id="id_object_set-0-collection">
                </td>
            </tr>
            <tr class="form-row has_original dynamic-object_set" id="object_set-1">
                <td class="field-inventory">
                    <input type="text" name="object_set-1-inventory" class="vTextField" maxlength="255"
                        id="id_object_set-1-inventory">
                </td>
                <td class="field-collection">
                    <input type="text" name="object_set-1-collection" class="vTextField" maxlength="255" disabled=""
                        id="id_object_set-1-collection">
                </td>
            </tr>
        </tbody>
    </table>
</div>
`;
