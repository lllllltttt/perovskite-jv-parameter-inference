function e2v3_comsol_batch(port, chunkCsv, curveDir, logPath)
% e2v3_comsol_batch.m  (E2-v3 worker: two FINER mesh grades m=0.18 / m=0.125)
% =========================================================================
%  Third-round addition to the E2 mesh chain (round-2 solved m=0.35/0.25).
%  Reads the v3 fine-mesh manifest chunk; for every row it assigns the 9
%  physical params with the exact validated unit recipe, scales BOTH mesh1
%  Size features ('size' and 'size1' vertex override) hmax/hmin by m, rebuilds
%  mesh1, sets the Stationary relative tolerance stol on sol1 's1' (1e-6),
%  and runs model.sol('sol1').runAll (recompile + 131-pt V_app sweep) -- the
%  round-2 validated mesh route (runAll == study.run to <=1e-7 after stol set).
%
%  Element-size bases are read from the loaded (frozen, read-only) model via
%  feat.getDouble (6.89/1.06 'size', 3.55/0.53 'size1' nm) and never hardcoded.
%  The frozen model file is never modified.
%
%  Per row writes  row_%05d.csv  in curveDir:
%     # rowid=...,test_index=...,level_type=...,level=...,mesh_size_factor=...,
%       stol=...,status=ok|fail,elapsed_s=...,nelem=...,nvtx=...,unit=A/m2,n=131
%     131 J values (%.10g).  status=fail rows carry msg and no data.
%
%  This worker is a byte-for-byte copy of the round-2 e2v2_comsol_batch.m
%  logic (renamed, qc removed, no tol rows).
% =========================================================================
ROOT       = 'E:\project\work1';
MODEL_FILE = fullfile(ROOT, 'matlab&mph', '1D_PSC_wen.mph');
CSV_PARAMS   = {'mu_n','mu_p','tau_n','tau_p','Nc','Nv','tau_ETL','tau_HTL','rad_c'};
MODEL_PARAMS = {'mu_n_pvk','mu_p_pvk','tau_n_pvk','tau_p_pvk', ...
                'Nc_eff_pvk','Nv_eff_pvk','tau_ETL','tau_HTL','rad_c'};
SET_UNIT     = {'[m^2/(V*s)]','[m^2/(V*s)]','[s]','[s]','[1/m^3]','[1/m^3]','[s]','[s]','[m^3/s]'};
RAD_C_FACTOR = 1e-6;
NGRID        = 131;

addpath('E:\comsol6_3\COMSOL63\Multiphysics\mli');
mphstart(port);
import com.comsol.model.*
import com.comsol.model.util.*

T = readtable(chunkCsv);
model = mphload(MODEL_FILE);
fid = fopen(logPath, 'a');
fprintf(fid, 'worker port=%d chunk=%s rows=%d model loaded %s\n', ...
        port, chunkCsv, height(T), datestr(now));

base = e2_mesh_bases(model);                 % size.hmax/hmin, size1.hmax/hmin

for i = 1:height(T)
    row   = T(i, :);
    rowid = double(row.rowid);
    ti    = double(row.test_index);
    m     = double(row.mesh_size_factor);
    stol  = double(row.stol);
    ltype = char(row.level_type);
    lev   = char(row.level);
    e2_set_params(model, row);
    try
        e2_set_mesh(model, base, m);
        model.mesh('mesh1').run;
        [nelem, nvtx] = e2_stats(model);
    catch ME
        e2_write_fail(curveDir, rowid, ti, ltype, lev, m, stol, toc(tic), ...
                      ['mesh: ' ME.message], fid);
        continue;
    end
    try
        model.sol('sol1').feature('s1').set('stol', stol);
    catch ME
        e2_write_fail(curveDir, rowid, ti, ltype, lev, m, stol, toc(tic), ...
                      ['stol set: ' ME.message], fid);
        continue;
    end
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
disp('e2v3_comsol_batch done');
end

% ---- helpers (verbatim round-2) -------------------------------------------------
function e2_set_params(model, row)
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
f  = @(tag) model.mesh('mesh1').feature(tag);
base.size.hmax  = e2_getnum(f('size'), 'hmax');
base.size.hmin  = e2_getnum(f('size'), 'hmin');
base.size1.hmax = e2_getnum(f('size1'), 'hmax');
base.size1.hmin = e2_getnum(f('size1'), 'hmin');
fprintf('E2-v3 mesh bases size=(%.5g,%.5g) size1=(%.5g,%.5g)\n', ...
        base.size.hmax, base.size.hmin, base.size1.hmax, base.size1.hmin);
end

function v = e2_getnum(feat, prop)
% mesh-feature element sizes MUST be read with getDouble (verified on live
% 6.3 server; .get(prop) throws on MeshFeatureClient).
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
