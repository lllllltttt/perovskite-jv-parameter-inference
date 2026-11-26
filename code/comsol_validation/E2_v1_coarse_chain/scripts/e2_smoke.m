function e2_smoke(port)
% e2_smoke.m -- validate the FULL per-row E2 route on ONE row (sample 5808 ref,
% mesh_size_factor=1.0, stol=1e-6) exactly as e2_comsol_batch does it, then diff
% the runAll curve against the archived E1 study.run baseline (row_00006.csv).
% Expected agreement ~1e-7 mA/cm2 (the E1 toolchain gate level).
addpath('E:\comsol6_3\COMSOL63\Multiphysics\mli');
mphstart(port);
import com.comsol.model.*
import com.comsol.model.util.*
ROOT       = 'E:\project\work1';
MODEL_FILE = fullfile(ROOT, 'matlab&mph', '1D_PSC_wen.mph');
E1CUR      = 'E:\project\work1\supplementary_validation\E1\outputs\curves\row_00006.csv';

model = mphload(MODEL_FILE);

% ---- params for sample 5808 (frozen; manifest rowid 0) --------------------
CSV_PARAMS   = {'mu_n','mu_p','tau_n','tau_p','Nc','Nv','tau_ETL','tau_HTL','rad_c'};
MODEL_PARAMS = {'mu_n_pvk','mu_p_pvk','tau_n_pvk','tau_p_pvk', ...
                'Nc_eff_pvk','Nv_eff_pvk','tau_ETL','tau_HTL','rad_c'};
SET_UNIT     = {'[m^2/(V*s)]','[m^2/(V*s)]','[s]','[s]','[1/m^3]','[1/m^3]','[s]','[s]','[m^3/s]'};
vals = [2.95e-05, 1.53e-05, 8.07e-05, 2.35e-05, 1.07e26, 3.85e25, 2.45e-09, 4.69e-14, 3.56e-10];
for k = 1:numel(MODEL_PARAMS)
    v = vals(k);
    if strcmp(MODEL_PARAMS{k}, 'rad_c'), v = v * 1e-6; end
    model.param.set(MODEL_PARAMS{k}, sprintf('%e%s', v, SET_UNIT{k}));
end

% ---- mesh at m=1 (frozen) -------------------------------------------------
base.size.hmax  = model.mesh('mesh1').feature('size').getDouble('hmax');
base.size.hmin  = model.mesh('mesh1').feature('size').getDouble('hmin');
base.size1.hmax = model.mesh('mesh1').feature('size1').getDouble('hmax');
base.size1.hmin = model.mesh('mesh1').feature('size1').getDouble('hmin');
model.mesh('mesh1').feature('size').set('hmax', base.size.hmax);
model.mesh('mesh1').feature('size').set('hmin', base.size.hmin);
model.mesh('mesh1').feature('size1').set('hmax', base.size1.hmax);
model.mesh('mesh1').feature('size1').set('hmin', base.size1.hmin);
model.mesh('mesh1').run;
st = mphmeshstats(model, 'mesh1');
ne = sum(st.numelem(strcmp(st.types,'edg')));

% ---- tolerance + solve via runAll -----------------------------------------
model.sol('sol1').feature('s1').set('stol', 1e-6);
t0 = tic;
model.sol('sol1').runAll;
dt = toc(t0);
J = double(mphglobal(model, 'semi.J0_1')).';
Jma = J(:) * 0.1;                    % column, A/m2 -> mA/cm2
fprintf('smoke runAll ok nelem=%d dt=%.1f s n=%d\n', ne, dt, numel(Jma));
fprintf('Jma  min=%.4f max=%.4f mean=%.4f\n', min(Jma), max(Jma), mean(Jma));

% ---- diff vs archived E1 study.run baseline --------------------------------
fid = fopen(E1CUR, 'r');
C = textscan(fid, '%f', 'HeaderLines', 1); fclose(fid);
Jb = C{1}(:) * 0.1;                  % column
fprintf('Jb   min=%.4f max=%.4f mean=%.4f n=%d\n', min(Jb), max(Jb), mean(Jb), numel(Jb));
if numel(Jb) ~= numel(Jma)
    fprintf('LENGTH MISMATCH baseline=%d runAll=%d\n', numel(Jb), numel(Jma));
    return;
end
d    = abs(Jma - Jb);
df   = abs(Jma - flipud(Jb));        % reverse-order check
fprintf('diff same-order : rmse=%.3e mA/cm2  max|d|=%.3e\n', sqrt(mean(d.^2)),  max(d(:)));
fprintf('diff flip(Jb)   : rmse=%.3e mA/cm2  max|d|=%.3e\n', sqrt(mean(df.^2)), max(df(:)));
fprintf('Jma[1]=%.6f Jma[61]=%.6f Jma[131]=%.6f  Jb[1]=%.6f Jb[61]=%.6f Jb[131]=%.6f\n', ...
        Jma(1), Jma(61), Jma(end), Jb(1), Jb(61), Jb(end));
try ModelUtil.remove(model.tag); catch; end
disp('e2_smoke done');
end
