addpath('E:\comsol6_3\COMSOL63\Multiphysics\mli');
mphstart(2039);
import com.comsol.model.*
import com.comsol.model.util.*
model = mphload('E:\project\work1\matlab&mph\1D_PSC_wen.mph');
for ci = 1:2
    tag = sprintf('mc%d', ci);
    f = model.physics('semi').feature(tag);
    fprintf('--- %s label=%s ---\n', tag, char(f.label()));
    for pn = {'TerminalName','TerminalType','V0','ContactType','Phi_B','Phi','ContactResistance'}
        try, fprintf('  %s = %s\n', char(pn), char(f.getString(char(pn)))); 
        catch, fprintf('  %s = [getString failed] ', char(pn)); 
               try, fprintf('%s\n', char(f.get(char(pn)))); catch, fprintf('NA\n'); end
        end
    end
end
try, ModelUtil.remove(model.tag); catch, end
