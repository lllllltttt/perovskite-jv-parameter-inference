%% auditC_live_probe.m  (Audit C: electrode/contact physical configuration)
% =========================================================================
%  Live COMSOL probe used to settle Audit C. Read-only wrt. the frozen model:
%    (1) load the frozen model matlab&mph\1D_PSC_wen.mph,
%    (2) print the geometry-vertex -> x  map  (vertex entity index -> nm),
%    (3) print the two metal contacts (semi mc1 'Ag', mc2 'FTO'):
%          selection entities (0D vertex set), terminal name/type, V0,
%          and the common Richardson-ohmic parameter block,
%    (4) toolchain validation: assign the sample test_index=269 true
%          parameters (verbatim forward_validation_unbiased CSV row) and
%          re-solve; compare J(V) to the stored frozen MAT
%          Sample_00269_true.mat (RMSE must be ~0).
%
%  REQUIREMENT: a COMSOL server must already be listening on PORT before
%  this runs (mphstart only connects):
%     comsolmphserver.exe -port 2039 ...
%  Run: matlab -batch "run('...\auditC_live_probe.m')"
%  Transcript is captured to stdout (redirect to auditC_log.txt by caller).
%  The frozen model file is never modified.
% =========================================================================
ROOT       = fileparts(fileparts(fileparts(mfilename('fullpath')))); % E:\project\work1
MODEL_FILE = fullfile(ROOT, 'matlab&mph', '1D_PSC_wen.mph');
CSV_TRUE   = fullfile(ROOT, 'forward_validation_unbiased', 'comsol_true_parameters.csv');
MAT_TRUE   = fullfile(ROOT, 'forward_validation_unbiased', 'comsol_true', 'Sample_00269_true.mat');
PORT       = 2039;

addpath('E:\comsol6_3\COMSOL63\Multiphysics\mli');
mphstart(PORT);
import com.comsol.model.*
import com.comsol.model.util.*

model = mphload(MODEL_FILE);
fprintf('loaded %s\n', MODEL_FILE);

%% ---- (2) geometry vertex entity -> x map ------------------------------
g = model.geom('geom1');
vc = [];
try, vc = double(g.getVertexCoord()); catch ME, fprintf('getVertexCoord NA: %s\n', ME.message); end
if isempty(vc)
    try, vc = double(g.getVertexCoords()); catch ME, fprintf('getVertexCoords NA: %s\n', ME.message); end
end
fprintf('vertex-coord matrix size: %s\n', mat2str(size(vc)));
if ~isempty(vc)
    for k = 1:size(vc, 2)
        fprintf('  vertex %3d   x = %14.6f   (nm: %.6f)\n', k, vc(1, k), vc(1, k)*1e9);
    end
end

%% ---- (3) contact facts -------------------------------------------------
semi = model.physics('semi');
fprintf('\ncontact facts (physics semi):\n');
for ci = 1:2
    tag = sprintf('mc%d', ci);
    f   = semi.feature(tag);
    lab = char(f.label());
    ent = sort(double(f.selection().entities()));
    fprintf('  [%s] label=%s  selection entities={%s}\n', tag, lab, num2str(ent));
    props = {'TerminalName','TerminalType','V0','ContactType','SpecifyUsing', ...
             'SpecifyBarrierHeight','Phi_B','Phi','vsnin','vspin', ...
             'Astar_n','Astar_p','ContactResistance','rho_c'};
    for p = 1:numel(props)
        pn = props{p};
        try
            v = f.get(pn);
            if isa(v, 'java.lang.String'), v = char(v); end
            if isnumeric(v), s = mat2str(v); else, s = char(v); end
        catch
            s = 'NA';
        end
        fprintf('        %-22s = %s\n', pn, s);
    end
end

%% ---- (4) toolchain validation: reproduce sample test_index=269 ---------
T = readtable(CSV_TRUE);
r = T(T.sample_id == 269, :);
CSV_PARAMS   = {'mu_n','mu_p','tau_n','tau_p','Nc','Nv','tau_ETL','tau_HTL','rad_c'};
MODEL_PARAMS = {'mu_n_pvk','mu_p_pvk','tau_n_pvk','tau_p_pvk', ...
                'Nc_eff_pvk','Nv_eff_pvk','tau_ETL','tau_HTL','rad_c'};
SET_UNIT     = {'[m^2/(V*s)]','[m^2/(V*s)]','[s]','[s]','[1/m^3]','[1/m^3]','[s]','[s]','[m^3/s]'};
RAD_C_FACTOR = 1e-6;
for k = 1:numel(MODEL_PARAMS)
    v = r.(CSV_PARAMS{k});
    if strcmp(MODEL_PARAMS{k}, 'rad_c'), v = v * RAD_C_FACTOR; end
    model.param.set(MODEL_PARAMS{k}, sprintf('%e%s', v, SET_UNIT{k}));
end
t0 = tic;
model.study('std1').run;
dt = toc(t0);
Jout = double(mphglobal(model, 'semi.J0_1')).';
fprintf('\ntoolchain check: solved test_index=269 in %.1f s\n', dt);
fprintf('  J(0) = %.6f A/m^2   (frozen DB J_test_raw[269] = 22.413123 A/m^2)\n', Jout(1));
if exist(MAT_TRUE, 'file')
    M    = load(MAT_TRUE);
    Jref = double(M.J(:)).';
    fprintf('  vs stored Sample_00269_true.mat: rmse = %.3e  max|d| = %.3e  (n=%d)\n', ...
            sqrt(mean((Jout-Jref).^2)), max(abs(Jout-Jref)), numel(Jout));
end

try, ModelUtil.remove(model.tag); catch, end
disp('auditC_live_probe done');
