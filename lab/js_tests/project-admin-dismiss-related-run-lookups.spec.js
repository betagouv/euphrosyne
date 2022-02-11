import { jest } from "@jest/globals";
import {
  dismissChangeRelatedRunPopup,
  dismissDeleteRelatedRunPopup,
} from "../assets/js/run-inline-handlers.js";

const RUNS_HTML = `
<div class="js-inline-admin-formset inline-group" id="runs-group" data-inline-type="stacked" data-inline-formset="{&quot;name&quot;: &quot;#runs&quot;, &quot;options&quot;: {&quot;prefix&quot;: &quot;runs&quot;, &quot;addText&quot;: &quot;Ajouter un objet Run suppl\u00e9mentaire&quot;, &quot;deleteText&quot;: &quot;Enlever&quot;}}">
<fieldset class="module ">
  
    <h2>Runs</h2>
  
<input type="hidden" name="runs-TOTAL_FORMS" value="2" id="id_runs-TOTAL_FORMS" autocomplete="off"><input type="hidden" name="runs-INITIAL_FORMS" value="1" id="id_runs-INITIAL_FORMS"><input type="hidden" name="runs-MIN_NUM_FORMS" value="0" id="id_runs-MIN_NUM_FORMS" autocomplete="off"><input type="hidden" name="runs-MAX_NUM_FORMS" value="1000" id="id_runs-MAX_NUM_FORMS" autocomplete="off">


<div id="runs" class="two-boxes-inline-container">
<div class="inline-related last-related dynamic-runs" id="runs-0">
  <h3><b>Run:</b> <span class="inline_label label-test-class">1<a href="/admin/lab/run/92/change/?_popup=1" class="inlinechangelink related-run-link">Modification</a></span>
      
    
  <span><a class="inline-deletelink" href="#" style="display: inline;">Enlever</a></span></h3>
  
  
    <fieldset class="module aligned ">
      
      
      <div class="flex-container">
        
          <div class="form-row field-start_date">
            
            
              <div>
                
                <div class="readonly">11 février 2022 09:00</div>
              </div>
            
          </div>
        
          <div class="form-row field-end_date">
            
            
              <div>
                
                <div class="readonly">11 février 2022 18:00</div>
              </div>
            
          </div>
        
      </div>
    </fieldset>
  
    <fieldset class="module aligned ">
      <h3>Conditions expérimentales</h3>
      
      <div class="flex-container">
        
          <div class="form-row field-particle_type">
            
            
              <div>
                
                <div class="readonly">Proton</div>
              </div>
            
          </div>
        
          <div class="form-row field-energy_in_keV">
            
            
              <div>
                
                <div class="readonly">1</div>
              </div>
            
          </div>
        
          <div class="form-row field-beamline beamline-test-class">
            
            
              <div>
                
                <div class="readonly">Microbeam</div>
              </div>
            
          </div>
        
      </div>
    </fieldset>
  
  <input type="hidden" name="runs-0-id" id="id_runs-0-id">
  <input type="hidden" name="runs-0-project" value="2" id="id_runs-0-project">
</div><div class="inline-related last-related dynamic-runs" id="runs-1">
  <h3><b>Run:</b> <span class="inline_label">5<a href="/admin/lab/run/95/change/?_popup=1" class="inlinechangelink related-run-link">Modification</a></span>
      
    
  <span><a class="inline-deletelink" href="#" style="display: inline;">Enlever</a></span></h3>
  
  
    <fieldset class="module aligned ">
      
      
      <div class="flex-container">
        
          <div class="form-row field-start_date">
            
            
              <div>
                
                <div class="readonly">11 février 2022 09:00</div>
              </div>
            
          </div>
        
          <div class="form-row field-end_date">
            
            
              <div>
                
                <div class="readonly">11 février 2022 18:00</div>
              </div>
            
          </div>
        
      </div>
    </fieldset>
  
    <fieldset class="module aligned ">
      <h3>Conditions expérimentales</h3>
      
      <div class="flex-container">
        
          <div class="form-row field-particle_type">
            
            
              <div>
                
                <div class="readonly">Deuton</div>
              </div>
            
          </div>
        
          <div class="form-row field-energy_in_keV">
            
            
              <div>
                
                <div class="readonly">5</div>
              </div>
            
          </div>
        
          <div class="form-row field-beamline">
            
            
              <div>
                
                <div class="readonly">Microbeam</div>
              </div>
            
          </div>
        
      </div>
    </fieldset>
  
  <input type="hidden" name="runs-1-id" id="id_runs-1-id">
  <input type="hidden" name="runs-1-project" value="2" id="id_runs-1-project">
</div><div class="inline-related empty-form last-related" id="runs-empty">
  <h3><b>Run:</b> <span class="inline_label">#5</span>
      
    
  </h3>
  
  
    <fieldset class="module aligned ">
      
      
      <div class="flex-container">
        
          <div class="form-row field-start_date">
            
            
              <div>
                
                <div class="readonly">-</div>
              </div>
            
          </div>
        
          <div class="form-row field-end_date">
            
            
              <div>
                
                <div class="readonly">-</div>
              </div>
            
          </div>
        
      </div>
    </fieldset>
  
    <fieldset class="module aligned ">
      <h3>Conditions expérimentales</h3>
      
      <div class="flex-container">
        
          <div class="form-row field-particle_type">
            
            
              <div>
                
                <div class="readonly">-</div>
              </div>
            
          </div>
        
          <div class="form-row field-energy_in_keV">
            
            
              <div>
                
                <div class="readonly">-</div>
              </div>
            
          </div>
        
          <div class="form-row field-beamline">
            
            
              <div>
                
                <div class="readonly">Microbeam</div>
              </div>
            
          </div>
        
      </div>
    </fieldset>
  
  <input type="hidden" name="runs-__prefix__-id" id="id_runs-__prefix__-id">
  <input type="hidden" name="runs-__prefix__-project" value="2" id="id_runs-__prefix__-project">
</div><div class="add-row" style="display: block;"><a href="#">Ajouter un objet Run supplémentaire</a></div>
</div>
<div class="add-row">
  <a id="add_runs" href="/admin/lab/run/add/?_popup=1&amp;project=2" class="related-run-link">Ajouter un nouveau run</a>
</div>
</fieldset>
</div>
`;

describe("dismissChangeRelatedRunPopup", () => {
  it("updates the indexes", () => {
    const mockWindow = {
      close: jest.fn(),
    };
    document.body.innerHTML = RUNS_HTML;

    dismissChangeRelatedRunPopup(mockWindow, {
      id: "92",
      label: "new label",
      beamline: "new beamline",
    });

    expect(document.querySelector(".label-test-class").textContent).toMatch(
      /^new label/
    );
    expect(document.querySelector(".beamline-test-class").textContent).toMatch(
      /^\s*new beamline\s*$/
    );
  });
});

describe("dismissDeleteRelatedRunPopup", () => {
  it("removes the div", () => {
    const mockWindow = {
      close: jest.fn(),
    };
    document.body.innerHTML = RUNS_HTML;

    const initialInlineLabelsLength = document
      .getElementById("runs-group")
      .querySelectorAll(".inline-related").length;

    dismissDeleteRelatedRunPopup(mockWindow, "95");

    expect(
      document.getElementById("runs-group").querySelectorAll(".inline-related")
        .length
    ).toEqual(initialInlineLabelsLength - 1);

    expect(
      Array.from(document.querySelectorAll(".inline-related")).map((e) => e.id)
    ).toEqual(["runs-0", "runs-empty"]);
  });
  it("updates the indexes", () => {
    const mockWindow = {
      close: jest.fn(),
    };
    document.body.innerHTML = RUNS_HTML;

    const initialInlineLabelsLength = document
      .getElementById("runs-group")
      .querySelectorAll(".inline-related").length;

    dismissDeleteRelatedRunPopup(mockWindow, "92");

    expect(
      document.getElementById("runs-group").querySelectorAll(".inline-related")
        .length
    ).toEqual(initialInlineLabelsLength - 1);

    expect(
      Array.from(document.querySelectorAll(".inline-related")).map((e) => e.id)
    ).toEqual(["runs-0", "runs-empty"]);
  });
});
