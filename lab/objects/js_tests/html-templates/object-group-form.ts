export const template: string = `
<form method="post" id="objectgroup_form" novalidate enctype="multipart/form-data">
    <div>
        <input type="hidden" name="_popup" value="1">
        <input type="hidden" name="_to_field" value="id">
        <fieldset class="module aligned ">
            <div class="description">Un lot d'objet peut contenir plusieurs objets ou un seul uniquement. Il est
                possible de spécifier la collection et l'inventaire au niveau du group ou pour chaque objet. Le champ
                dédié au nombre total par objet est utilse lors d'un ajout de plusieurs objets similaires.</div>
            <div class="form-row field-add_type">
                <div>
                    <label for="id_add_type_0"></label>
                    <ul class="fr-tag-list">
                        <input type="hidden" name="add_type" value="SINGLE_OBJECT" id="id_add_type" />
                        <button type="button" class="fr-tag choice-tag" aria-pressed="true" data-value="SINGLE_OBJECT">
                            Objet unique
                        </button> <button type="button" class="fr-tag choice-tag" aria-pressed="false"
                            data-value="OBJECT_GROUP">
                            Groupe d&#x27;objets
                        </button>
                    </ul>
                </div>
            </div>
            <div class="form-row field-label">
                <div>
                    <label class="required" for="id_label">Libellé :</label> <input type="text" name="label"
                        class="vTextField" maxlength="255" required id="id_label">
                </div>
            </div>
            <div class="form-row hidden field-object_count">
                <div>
                    <label class="required" for="id_object_count">Nombre d&#x27;objets :</label> <input type="hidden"
                        name="object_count" value="1" id="id_object_count">
                </div>
            </div>
            <div class="form-row field-dating">
                <div>
                    <label class="required" for="id_dating">Datation :</label> <input type="text" name="dating"
                        class="vTextField" maxlength="255" required id="id_dating">
                </div>
            </div>
            <div class="form-row field-materials">
                <div>
                    <label class="required" for="id_materials">Matériaux :</label>
                    <div class="tags-input">
                        <input type="text" class="tags-input__input" size="1" required id="id_materials">
                        <input type="hidden" name="materials" required id="id_materials">
                    </div><input type="hidden" name="initial-materials" id="initial-id_materials">
                    <div class="help">Séparez chaque matériau par une virgule</div>
                </div>
            </div>
            <div class="form-row field-discovery_place">
                <div>
                    <label for="id_discovery_place">Lieu de découverte :</label> <input type="text"
                        name="discovery_place" class="vTextField" maxlength="255" id="id_discovery_place">
                </div>
            </div>
            <div class="form-row field-inventory">
                <div>
                    <label for="id_inventory">Inventaire :</label> <input type="text" name="inventory"
                        class="vTextField" maxlength="255" id="id_inventory">
                </div>
            </div>
            <div class="form-row field-collection">
                <div>
                    <label for="id_collection">Collection :</label> <input type="text" name="collection"
                        class="vTextField" maxlength="255" id="id_collection">
                </div>
            </div>
        </fieldset>
        <fieldset class="module aligned hidden" id="object_set-fieldset">
            <section class="fr-accordion">
                <h3 class="fr-accordion__title">
                    <button type="button" class="fr-accordion__btn" aria-expanded="false"
                        aria-controls="differentiation-accordion">
                        Différencier les objets
                    </button>
                </h3>
                <div class="fr-collapse" id="differentiation-accordion">
                    <div class="js-inline-admin-formset inline-group overflow-auto" id="object_set-group"
                        data-inline-type="tabular"
                        data-inline-formset="{&quot;name&quot;: &quot;#object_set&quot;, &quot;options&quot;: {&quot;prefix&quot;: &quot;object_set&quot;, &quot;addText&quot;: &quot;Ajouter un autre lot&quot;, &quot;deleteText&quot;: &quot;Enlever&quot;}}">
                        <div class="tabular inline-related last-related">
                            <input type="hidden" name="object_set-TOTAL_FORMS" value="0"
                                id="id_object_set-TOTAL_FORMS"><input type="hidden" name="object_set-INITIAL_FORMS"
                                value="0" id="id_object_set-INITIAL_FORMS"><input type="hidden"
                                name="object_set-MIN_NUM_FORMS" value="0" id="id_object_set-MIN_NUM_FORMS"><input
                                type="hidden" name="object_set-MAX_NUM_FORMS" value="1000"
                                id="id_object_set-MAX_NUM_FORMS">
                            <table>
                                <thead>
                                    <tr>
                                        <th class="original"></th>
                                        <th class="column-label required">Libellé </th>
                                        <th class="column-inventory">Inventaire </th>
                                        <th class="column-collection">Collection </th>
                                        <th>Supprimer ?</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr class="form-row  empty-form" id="object_set-empty">
                                        <td class="original"> <input type="hidden" name="object_set-__prefix__-id"
                                                id="id_object_set-__prefix__-id">
                                            <input type="hidden" name="object_set-__prefix__-group"
                                                id="id_object_set-__prefix__-group">
                                        </td>
                                        <td class="field-label">
                                            <input type="text" name="object_set-__prefix__-label" class="vTextField"
                                                maxlength="255" id="id_object_set-__prefix__-label">
                                        </td>
                                        <td class="field-inventory">
                                            <input type="text" name="object_set-__prefix__-inventory" class="vTextField"
                                                maxlength="255" id="id_object_set-__prefix__-inventory">
                                        </td>
                                        <td class="field-collection">
                                            <input type="text" name="object_set-__prefix__-collection"
                                                class="vTextField" maxlength="255"
                                                id="id_object_set-__prefix__-collection">
                                        </td>
                                        <td class="delete"></td>
                                    </tr>
                                    <tr class="add-row">
                                        <td colspan="5"><a href="#">Ajouter un autre lot</a></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>
        </fieldset>
        <div class="submit-row"> <input type="submit" value="Enregistrer" class="default" name="_save">
        </div>
    </div>
</form>
`;
