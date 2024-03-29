export const snippet = `
<tr class="form-row has_original dynamic-{{ formsetPrefix }}" id="{{ formsetPrefix }}-{{ formIndex }}">
    <td class="original">
        <p>
            {{ formsetPrefix }} object ({{ objectId }})
        </p>
        <input type="hidden" name="{{ formsetPrefix }}-{{ formIndex }}-id" value="{{ objectId }}"
            id="id_{{ formsetPrefix }}-{{ formIndex }}-id">
        <input type="hidden" name="{{ formsetPrefix }}-{{ formIndex }}-{{ parentObjectName }}"
            value="{{ parentObjectId }}" id="id_{{ formsetPrefix }}-{{ formIndex }}-{{ parentObjectName }}">
    </td>
    <td class="field-{{ objectName }}">
        <p>
            <a href="{{ objectChangeUrl }}">
                {{ objectRepr }}
            </a>
        </p>
    </td>
    <td class="delete"><input type="checkbox" name="{{ formsetPrefix }}-{{ formIndex }}-DELETE"
            id="id_{{ formsetPrefix }}-{{ formIndex }}-DELETE"></td>
</tr>
`;
