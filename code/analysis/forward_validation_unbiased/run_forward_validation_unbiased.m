%% run_forward_validation_unbiased.m
% =========================================================================
%  UNBIASED FORWARD VALIDATION -- COMSOL batch run (LOCAL, server-exact recipe)
% =========================================================================
%  Replicates the original database-generation recipe (server script
%  run_PSC_9D_8.m) exactly:
%     * parameter assignment uses EXPLICIT SI units:
%         mu_n_pvk/mu_p_pvk    %e[m^2/(V*s)]     (LHS CSV already in m2/V/s)
%         tau_n_pvk/tau_p_pvk  %e[s]
%         Nc_eff_pvk/Nv_eff_pvk %e[1/m^3]
%         tau_ETL/tau_HTL      %e[s]             (CSV column tau_ETL/tau_HTL)
%         rad_c                %e[m^3/s] with value *1e-6   (CSV column is cm3/s)
%     * study tag 'std1' ; J extracted via mphglobal(model, 'semi.J0_1')
%       (131 points, V = 0:0.01:1.3 ; J in A/m^2).
%
%  Model: E:\project\work1\matlab&mph\1D_PSC_wen.mph
%     (the model copied from the server that generated the database;
%      verified on sample test_index=269: COMSOL(true params) reproduces
%      J_test_raw[269] exactly, RMSE=0).
%
%  The model is loaded ONCE and reused across samples (the study run
%  overwrites the stored solution, so memory stays bounded).
%
%  Outputs:
%    comsol_pred/Sample_XXXXX_pred.mat    source = 'pred'
%    comsol_true/Sample_XXXXX_true.mat    source = 'true'  (control)
%  MAT fields: Index, source, test_index, model_version, param_input_file,
%    V_grid, mu_n_pvk ... rad_c (verbatim CSV values), J (A/m^2, 131x1).
%  Existing MAT files are NEVER overwritten (per-sample guard).
%
%  REQUIREMENT: a COMSOL server must be listening on the port below before
%  running (mphstart only CONNECTS to an existing server):
%     E:\comsol6_3\COMSOL63\Multiphysics\bin\win64\comsolmphserver.exe -port 2039
%  Run this file in MATLAB (R2024b) with COMSOL LiveLink for MATLAB 6.3:
%     matlab -batch "run('...\run_forward_validation_unbiased.m')"

%% ---- CONFIG -----------------------------------------------------------
ROOT        = pwd;                 % directory containing the CSVs + output dirs
MODEL_FILE  = 'E:\project\work1\matlab&mph\1D_PSC_wen.mph';
PORT        = 2039;
MODEL_TAG   = 'VAE_v6_unbiased_fwd_2026-08-23';
RUN_TRUE    = true;                % true-parameter control (spec section 13)

COMSOL_INPUT = fullfile(ROOT, 'comsol_input_parameters.csv');
TRUE_INPUT   = fullfile(ROOT, 'comsol_true_parameters.csv');
OUT_PRED     = fullfile(ROOT, 'comsol_pred');
OUT_TRUE     = fullfile(ROOT, 'comsol_true');
V_GRID       = (0:0.01:1.3).';     % 131 points, matches dataset grid

% CSV short names -> model global-parameter names (server recipe)
CSV_PARAMS  = {'mu_n','mu_p','tau_n','tau_p','Nc','Nv','tau_ETL','tau_HTL','rad_c'};
MODEL_PARAMS = {'mu_n_pvk','mu_p_pvk','tau_n_pvk','tau_p_pvk', ...
                'Nc_eff_pvk','Nv_eff_pvk','tau_ETL','tau_HTL','rad_c'};
% unit string / value transformation per parameter (SERVER-PROVEN)
SET_UNIT   = {'[m^2/(V*s)]','[m^2/(V*s)]','[s]','[s]','[1/m^3]','[1/m^3]','[s]','[s]','[m^3/s]'};
RAD_C_FACTOR = 1e-6;               % cm^3/s -> m^3/s (only applied to rad_c)

%% ---- connect to COMSOL server ----------------------------------------
addpath('E:\comsol6_3\COMSOL63\Multiphysics\mli');
mphstart(PORT);
import com.comsol.model.*
import com.comsol.model.util.*

model = mphload(MODEL_FILE);
fprintf('Loaded model: %s\n', MODEL_FILE);

%% ---- safe output dirs -------------------------------------------------
if ~exist(OUT_PRED, 'dir'), mkdir(OUT_PRED); end
if RUN_TRUE && ~exist(OUT_TRUE, 'dir'), mkdir(OUT_TRUE); end

total_tic = tic;

%% ---- Predicted params (the main cohort) -------------------------------
Tpred = readtable(COMSOL_INPUT);
fprintf('Predicted cohort: %d samples\n', height(Tpred));
for i = 1:height(Tpred)
    try
        solve_and_save(model, Tpred(i, :), 'pred', OUT_PRED, MODEL_PARAMS, ...
                       CSV_PARAMS, SET_UNIT, RAD_C_FACTOR, V_GRID, MODEL_TAG);
    catch ME
        fprintf('   [pred] sample %05d FAILED: %s\n', Tpred.sample_id(i), ME.message);
    end
    if mod(i, 5) == 0
        fprintf('   ... pred %d/%d, %.1f min elapsed\n', i, height(Tpred), toc(total_tic)/60);
    end
end

%% ---- True params (control, spec section 13) ---------------------------
if RUN_TRUE
    Ttrue = readtable(TRUE_INPUT);
    fprintf('True-parameter control: %d samples\n', height(Ttrue));
    for i = 1:height(Ttrue)
        try
            solve_and_save(model, Ttrue(i, :), 'true', OUT_TRUE, MODEL_PARAMS, ...
                           CSV_PARAMS, SET_UNIT, RAD_C_FACTOR, V_GRID, MODEL_TAG);
        catch ME
            fprintf('   [true] sample %05d FAILED: %s\n', Ttrue.sample_id(i), ME.message);
        end
        if mod(i, 5) == 0
            fprintf('   ... true %d/%d, %.1f min elapsed\n', i, height(Ttrue), toc(total_tic)/60);
        end
    end
end

try
    ModelUtil.remove(model.tag);
catch
end

fprintf('All done in %.1f min. MAT outputs in %s and %s\n', ...
        toc(total_tic)/60, OUT_PRED, OUT_TRUE);


%% =====================================================================
function solve_and_save(model, row, source, outDir, modelParams, csvParams, ...
                        setUnit, radFactor, Vgrid, modelTag)
    sampleID = row.sample_id;                 % = test_index
    fname = fullfile(outDir, sprintf('Sample_%05d_%s.mat', sampleID, source));
    if exist(fname, 'file')
        error('Refusing to overwrite existing MAT: %s', fname);
    end

    % assign parameters verbatim with the server-proven SI unit strings
    for k = 1:numel(modelParams)
        v = row.(csvParams{k});
        if strcmp(modelParams{k}, 'rad_c')
            v = v * radFactor;                % cm^3/s -> m^3/s
        end
        model.param.set(modelParams{k}, sprintf('%e%s', v, setUnit{k}));
    end

    % solve + extract (server-exact)
    model.study('std1').run;
    Jout = mphglobal(model, 'semi.J0_1');
    Jout = Jout(:);
    assert(numel(Jout) == 131, 'JV length = %d', numel(Jout));
    assert(~any(isnan(Jout)), 'NaN detected in J');

    % provenance + historical fields
    P = struct();
    P.Index             = sampleID;
    P.source            = source;
    P.test_index        = sampleID;
    P.model_version     = modelTag;
    P.param_input_file  = sprintf('comsol_%s_parameters.csv', source);
    P.V_grid            = Vgrid;
    P.mu_n_pvk          = row.mu_n;    P.mu_p_pvk = row.mu_p;
    P.tau_n_pvk         = row.tau_n;   P.tau_p_pvk = row.tau_p;
    P.Nc_eff_pvk        = row.Nc;      P.Nv_eff_pvk = row.Nv;
    P.tau_ETL           = row.tau_ETL; P.tau_HTL = row.tau_HTL;
    P.rad_c             = row.rad_c;
    P.J                 = Jout;        % A/m^2, 131 x 1
    save(fname, '-struct', 'P');
    fprintf('   [%s] sample %05d  J(0)=%.4f A/m^2  saved %s\n', ...
            source, sampleID, Jout(1), fname);
end
