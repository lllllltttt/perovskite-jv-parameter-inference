function e2_comsol_batch(port, chunkCsv, curveDir, logPath, qc)
% e2_comsol_batch.m  (E2 worker: mesh-resolution x solver-tolerance convergence)
% =========================================================================
%  Reads a chunk of the E2 job manifest.  For every row it assigns the 9
%  physical params with the exact validated unit recipe, applies the row's
%  mesh element-size factor m to BOTH mesh1 Size features ('size' default and
%  'size1' vertex override: hmax,hmin scaled by m), rebuilds mesh1, sets the
%  Stationary relative tolerance stol on sol1 feature 's1' (p:stol), and runs
%  the solver sequence with model.sol('sol1').runAll  (recompiles via the
%  embedded StudyStep st1 + solves the 131-pt V_app parametric sweep).
%
%  mesh_size_factor m:  >1 coarser, <1 finer, 1 = frozen (default 6.89/1.06 on
%  'size', 3.55/0.53 on 'size1' read at load, never hard-coded).
%  stol: Stationary relative tolerance (frozen 1e-6).
%
%  Per row a file  row_%05d.csv  is written in curveDir:
%     # rowid=...,test_index=...,level_type=...,level=...,mesh_size_factor=...,
%       stol=...,status=ok|fail,elapsed_s=...,nelem=...,unit=A/m2,n=131
%     131 J values (%.10g).  status=fail rows carry msg=... and no data.
%
%  When qc==1 the worker additionally performs ONE model.study('std1').run
%  solve (the proven E1/archive code path) at frozen settings for its first
%  row's parameter set, written as  qc_studyrun_%05d.csv  (rowid of the row),
%  so the runAll route can be validated against study.run on identical input.
%
%  REQUIREMENT: a COMSOL server must listen on PORT (restart after any client
%  disconnect).  The frozen model file is never modified (read-only load).
% =========================================================================
ROOT       = 'E:\project\work1';
MODEL_FILE = fullfile(ROOT, 'matlab&mph', '1D_PSC_wen.mph');
CSV_PARAMS   = {'mu_n','mu_p','tau_n','tau_p','Nc','Nv','tau_ETL','tau_HTL','rad_c'};
MODEL_PARAMS = {'mu_n_pvk','mu_p_pvk','tau_n_pvk','tau_p_pvk', ...
                'Nc_eff_pvk','Nv_eff_pvk','tau_ETL','tau_HTL','rad_c'};
SET_UNIT     = {'[m^2/(V*s)]','[m^2/(V*s)]','[s]','[s]','[1/m^3]','[1/m^3]','[s]','[s]','[m^3/s]'};
RAD_C_FACTOR = 1e-6;
NGRID        = 131;
if nargin < 5, qc = 0; end

addpath('E:\comsol6_3\COMSOL63\Multiphysics\mli');
mphstart(port);
import com.comsol.model.*
import com.comsol.model.util.*

T = readtable(chunkCsv);
model = mphload(MODEL_FILE);
fid = fopen(logPath, 'a');
fprintf(fid, 'worker port=%d chunk=%s rows=%d qc=%d model loaded %s\n', ...
        port, chunkCsv, height(T), qc, datestr(now));

% ---- capture frozen mesh element-size bases (exact, from the loaded model) --
base = e2_mesh_bases(model);                 % struct: size.hmax/hmin, size1.hmax/hmin

% ---- QC: study.run at frozen settings for the first row's params ------------
if qc == 1
    r0 = T(1, :);
    e2_set_params(model, r0);
    try
        t0 = tic; model.study('std1').run; dt = toc(t0);
        J  = double(mphglobal(model, 'semi.J0_1')).'; J = J(:).';
        [ne0, nv0] = e2_stats(model);
        fq = fullfile(curveDir, sprintf('qc_studyrun_%05d.csv', double(r0.rowid)));
        fw = fopen(fq, 'w');
        fprintf(fw, '# rowid=%d,test_index=%d,route=study.run,status=ok,elapsed_s=%.1f,nelem=%d,n=131\n', ...
                double(r0.rowid), double(r0.test_index), dt, ne0);
        fprintf(fw, '%.10g\n', J);
        fclose(fw);
        fprintf(fid, 'QC study.run row %d nelem %d dt %.1f s\n', double(r0.rowid), ne0, dt);
    catch ME
        fprintf(fid, 'QC study.run row %d FAILED: %s\n', double(r0.rowid), ME.message);
    end
    % reset mesh to frozen and solver to frozen for the main loop
    e2_set_mesh(model, base, 1.0);
    model.sol('sol1').feature('s1').set('stol', 1e-6);
end

% ---- main loop ---------------------------------------------------------------
for i = 1:height(T)
    row   = T(i, :);
    rowid = double(row.rowid);
    ti    = double(row.test_index);
    m     = double(row.mesh_size_factor);
    stol  = double(row.stol);
    ltype = char(row.level_type);
    lev   = char(row.level);
    % params
    e2_set_params(model, row);
    % mesh: set sizes = base * m and rebuild (always, keeps worker stateless)
    try
        e2_set_mesh(model, base, m);
        model.mesh('mesh1').run;
        [nelem, nvtx] = e2_stats(model);
    catch ME
        e2_write_fail(curveDir, rowid, ti, ltype, lev, m, stol, toc(tic), ...
                      ['mesh: ' ME.message], fid);
        continue;
    end
    % tolerance
    try
        model.sol('sol1').feature('s1').set('stol', stol);
    catch ME
        e2_write_fail(curveDir, rowid, ti, ltype, lev, m, stol, toc(tic), ...
                      ['stol set: ' ME.message], fid);
        continue;
    end
    % solve (runAll = recompile + parametric V_app sweep)
    t0 = tic; status = 'ok'; msg = '';
    try
        model.sol('sol1').runAll;
    catch ME
        status = 'fail';
        msg = strrep(ME.message, sprintf('\n'), ' | ');
        if numel(msg) > 200, msg = msg(1:200); end
    end
    dt = toc(t0);
    if strcmp(status, 'ok')
        J = double(mphglobal(model, 'semi.J0_1')).'; J = J(:).';
        if numel(J) ~= NGRID
            status = 'fail';
            msg = sprintf('unexpected sweep length n=%d (expect %d)', numel(J), NGRID);
        end
    end
    outFile = fullfile(curveDir, sprintf('row_%05d.csv', rowid));
    fw = fopen(outFile, 'w');
    if strcmp(status, 'ok')
        fprintf(fw, '# rowid=%d,test_index=%d,level_type=%s,level=%s,mesh_size_factor=%.5g,stol=%.3g,status=ok,elapsed_s=%.1f,nelem=%d,nvtx=%d,unit=A/m2,n=131\n', ...
                rowid, ti, ltype, lev, m, stol, dt, nelem, nvtx);
        fprintf(fw, '%.10g\n', J);
    else
        fprintf(fw, '# rowid=%d,test_index=%d,level_type=%s,level=%s,mesh_size_factor=%.5g,stol=%.3g,status=fail,elapsed_s=%.1f,nelem=%d,msg=%s\n', ...
                rowid, ti, ltype, lev, m, stol, dt, nelem, msg);
    end
    fclose(fw);
    fprintf(fid, 'row %d ti %d %s/%s m %.2f stol %.0e status %s nelem %d dt %.1f s\n', ...
            rowid, ti, ltype, lev, m, stol, status, nelem, dt);
    if mod(i, 10) == 0, fprintf(fid, '  progress %d/%d\n', i, height(T)); end
end
fclose(fid);
try ModelUtil.remove(model.tag); catch; end
disp('e2_comsol_batch done');
end

% ---- helpers -----------------------------------------------------------------
function e2_set_params(model, row)
% verbatim validated unit recipe (identical to e1_comsol_batch)
CSV_PARAMS   = {'mu_n','mu_p','tau_n','tau_p','Nc','Nv','tau_ETL','tau_HTL','rad_c'};
MODEL_PARAMS = {'mu_n_pvk','mu_p_pvk','tau_n_pvk','tau_p_pvk', ...
                'Nc_eff_pvk','Nv_eff_pvk','tau_ETL','tau_HTL','rad_c'};
SET_UNIT     = {'[m^2/(V*s)]','[m^2/(V*s)]','[s]','[s]','[1/m^3]','[1/m^3]','[s]','[s]','[m^3/s]'};
RAD_C_FACTOR = 1e-6;
for k = 1:numel(MODEL_PARAMS)
    v = double(row.(CSV_PARAMS{k}));
    if isnan(v)
        error('param %s NaN at rowid %d', CSV_PARAMS{k}, double(row.rowid));
    end
    if strcmp(MODEL_PARAMS{k}, 'rad_c'), v = v * RAD_C_FACTOR; end
    model.param.set(MODEL_PARAMS{k}, sprintf('%e%s', v, SET_UNIT{k}));
end
end

function base = e2_mesh_bases(model)
% read frozen element-size bases of both Size features
f  = @(tag) model.mesh('mesh1').feature(tag);
base.size.hmax  = e2_getnum(f('size'), 'hmax');
base.size.hmin  = e2_getnum(f('size'), 'hmin');
base.size1.hmax = e2_getnum(f('size1'), 'hmax');
base.size1.hmin = e2_getnum(f('size1'), 'hmin');
fprintf('E2 mesh bases size=(%.5g,%.5g) size1=(%.5g,%.5g)\n', ...
        base.size.hmax, base.size.hmin, base.size1.hmax, base.size1.hmin);
end

function v = e2_getnum(feat, prop)
% mesh-feature element sizes must be read with getDouble: .get(prop) throws
% "cannot use get to access property ... on MeshFeatureClient" (verified on a
% live 6.3 server; getDouble returns the exact frozen values 6.89/1.06/3.55/0.53).
v = feat.getDouble(prop);
if isnan(v) || isempty(v), error('cannot read mesh property %s', prop); end
end

function e2_set_mesh(model, base, m)
f  = @(tag) model.mesh('mesh1').feature(tag);
f('size').set('hmax',  base.size.hmax  * m);
f('size').set('hmin',  base.size.hmin  * m);
f('size1').set('hmax', base.size1.hmax * m);
f('size1').set('hmin', base.size1.hmin * m);
end

function [nelem, nvtx] = e2_stats(model)
stats = mphmeshstats(model, 'mesh1');
n = stats.numelem; tp = stats.types;
k = strcmp(tp, 'edg');
nelem = double(sum(n(k)));
nvtx  = double(sum(n(strcmp(tp, 'vtx'))));
if isempty(nelem), nelem = 0; end
if isempty(nvtx), nvtx = 0; end
end

function e2_write_fail(curveDir, rowid, ti, ltype, lev, m, stol, dt, msg, fid)
outFile = fullfile(curveDir, sprintf('row_%05d.csv', rowid));
fw = fopen(outFile, 'w');
fprintf(fw, '# rowid=%d,test_index=%d,level_type=%s,level=%s,mesh_size_factor=%.5g,stol=%.3g,status=fail,elapsed_s=%.1f,nelem=0,msg=%s\n', ...
        rowid, ti, ltype, lev, m, stol, dt, msg);
fclose(fw);
fprintf(fid, 'row %d ti %d %s/%s FAIL %s\n', rowid, ti, ltype, lev, msg);
end
