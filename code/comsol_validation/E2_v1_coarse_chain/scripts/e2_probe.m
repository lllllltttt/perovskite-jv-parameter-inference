function e2_probe(port)
% e2_probe.m -- discover how to read mesh-feature element sizes on a live server.
% Connects on PORT, loads the frozen model read-only, and tries several accessors
% on the 'hmax'/'hmin' properties of mesh1 features 'size' and 'size1', then
% verifies a scaled set() + mesh rebuild + stats round-trip.
addpath('E:\comsol6_3\COMSOL63\Multiphysics\mli');
mphstart(port);
import com.comsol.model.*
import com.comsol.model.util.*
MODEL_FILE = 'E:\project\work1\matlab&mph\1D_PSC_wen.mph';
model = mphload(MODEL_FILE);
tags  = {'size','size1'};
props = {'hmax','hmin'};
pr = @(x, ft, fp) fprintf('%s:%s = %s\n', ft, fp, mat2str(x));
pf = @(ft, fp, ME) fprintf('%s:%s FAIL  %s\n', ft, fp, ME.message);

for fti = 1:numel(tags)
    ft = tags{fti};
    feat = model.mesh('mesh1').feature(ft);
    for fpi = 1:numel(props)
        fp = props{fpi};
        try
            x = feat.get(fp);        pr(x, ft, fp);
        catch ME,                   pf(ft, fp, ME);
        end
        try
            x = feat.getDouble(fp);  pr(x, ft, fp);
        catch ME,                   pf(ft, fp, ME);
        end
        try
            x = feat.getReal(fp);    pr(x, ft, fp);
        catch ME,                   pf(ft, fp, ME);
        end
        try
            x = feat.getString(fp);  pr(x, ft, fp);
        catch ME,                   pf(ft, fp, ME);
        end
    end
end

% round-trip: set size1 sizes to 0.7 * current frozen and count elements
f0 = model.mesh('mesh1').feature('size');
f1 = model.mesh('mesh1').feature('size1');
try
    s0h = f0.getDouble('hmax');
    s1h = f1.getDouble('hmax');
catch
    s0h = 6.89; s1h = 3.55;   % frozen XML values if reads fail
end
fprintf('chosen base size.hmax=%.5g size1.hmax=%.5g\n', s0h, s1h);
try
    model.mesh('mesh1').run;                      % frozen mesh
    st = mphmeshstats(model, 'mesh1');
    ne0 = sum(st.numelem(strcmp(st.types,'edg')));
    f0.set('hmax', s0h*0.7); f0.set('hmin', s0h*0.7/6.5);
    f1.set('hmax', s1h*0.7); f1.set('hmin', s1h*0.7/6.5);
    model.mesh('mesh1').run;
    st = mphmeshstats(model, 'mesh1');
    ne1 = sum(st.numelem(strcmp(st.types,'edg')));
    fprintf('SETOK frozen_ne=%d scaled_ne=%d (expect scaled>frozen)\n', ne0, ne1);
catch ME
    fprintf('SETFAIL %s\n', ME.message);
end
try ModelUtil.remove(model.tag); catch; end
disp('e2_probe done');
end
