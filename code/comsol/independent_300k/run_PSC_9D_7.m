function run_PSC_9D_7()

clear;
clc;

%% ==========================================
% COMSOL
%% ==========================================

addpath('/data1/comsol63/multiphysics/mli')

mphstart(2038)

import com.comsol.model.*
import com.comsol.model.util.*

%% ==========================================
% path
%% ==========================================

input_path = ...
'/home/student2/parameter/PSC_LHS_9D_interface_lifetimes_300000_5.csv';  % 新采样文件

mph_path = ...
'/home/student2/mph/1D_PSC_wen.mph';

result_dir = ...
'/home/student2/result-9D-interface-lifetimes-3/';                     % 新结果目录

if ~exist(result_dir,'dir')
    mkdir(result_dir);
end

%% ==========================================
% data
%% ==========================================

tbl = readtable(input_path);

N = 225000;                                            % 可根据需要调整

fprintf('Total samples = %d\n', N);

%% ==========================================
% range
%% ==========================================

start_idx = 150001;
end_idx   = N;

%% ==========================================
% timer
%% ==========================================

total_tic = tic;

%% ==========================================
% main loop
%% ==========================================

for i = start_idx:end_idx

    try

        sample_tic = tic;

        fprintf('\n');
        fprintf('Sample %d / %d\n', i, end_idx);

        %% -----------------------------
        % load model
        %% -----------------------------

        model = mphload(mph_path);

        %% -----------------------------
        % write parameters (界面寿命版)
        %% -----------------------------

        model.param.set( ...
            'mu_n_pvk', ...
            sprintf('%e[m^2/(V*s)]', ...
            tbl.mu_n_pvk(i)));

        model.param.set( ...
            'mu_p_pvk', ...
            sprintf('%e[m^2/(V*s)]', ...
            tbl.mu_p_pvk(i)));

        model.param.set( ...
            'tau_n_pvk', ...
            sprintf('%e[s]', ...
            tbl.tau_n_pvk(i)));

        model.param.set( ...
            'tau_p_pvk', ...
            sprintf('%e[s]', ...
            tbl.tau_p_pvk(i)));

        model.param.set( ...
            'Nc_eff_pvk', ...
            sprintf('%e[1/m^3]', ...
            tbl.Nc_eff_pvk(i)));

        model.param.set( ...
            'Nv_eff_pvk', ...
            sprintf('%e[1/m^3]', ...
            tbl.Nv_eff_pvk(i)));

        % ---- 界面寿命参数（取代缺陷密度） ----
        model.param.set( ...
            'tau_ETL', ...                    % COMSOL 中定义的参数名
            sprintf('%e[s]', ...
            tbl.tau_ETL_in(i)));              % 直接使用，单位为秒

        model.param.set( ...
            'tau_HTL', ...                    % COMSOL 中定义的参数名
            sprintf('%e[s]', ...
            tbl.tau_HTL_in(i)));

        % ---- 辐射复合系数（cm³/s → m³/s 转换） ----
        model.param.set( ...
            'rad_c', ...
            sprintf('%e[m^3/s]', ...
            tbl.rad_c_in(i) * 1e-6));         % 乘 1e-6 转换单位

        %% -----------------------------
        % solve
        %% -----------------------------

        model.study('std1').run;

        %% -----------------------------
        % extract JV
        %% -----------------------------

        J = mphglobal( ...
            model, ...
            'semi.J0_1');

        J = J(:);

        if length(J) ~= 131                   % 0~1.3V，步长0.01V，共131点

            error( ...
                'JV length = %d', ...
                length(J));

        end

        if any(isnan(J))

            error('NaN detected');

        end

        %% -----------------------------
        % save
        %% -----------------------------

        ResultData = struct();

        ResultData.Index      = i;
        ResultData.mu_n_pvk   = tbl.mu_n_pvk(i);
        ResultData.mu_p_pvk   = tbl.mu_p_pvk(i);
        ResultData.tau_n_pvk  = tbl.tau_n_pvk(i);
        ResultData.tau_p_pvk  = tbl.tau_p_pvk(i);
        ResultData.Nc_eff_pvk = tbl.Nc_eff_pvk(i);
        ResultData.Nv_eff_pvk = tbl.Nv_eff_pvk(i);
        ResultData.tau_ETL    = tbl.tau_ETL_in(i);   % 保存实际值
        ResultData.tau_HTL    = tbl.tau_HTL_in(i);
        ResultData.rad_c      = tbl.rad_c_in(i);     % 保留原始单位值
        ResultData.J          = J;

        save_name = fullfile( ...
            result_dir, ...
            sprintf('Sample_%05d.mat', i));

        save(save_name, '-struct', 'ResultData');

        %% -----------------------------
        % cleanup
        %% -----------------------------

        ModelUtil.remove(model.tag);

        %% -----------------------------
        % progress
        %% -----------------------------

        elapsed = toc(sample_tic);

        avg_time = toc(total_tic) / (i - start_idx + 1);

        eta_hour = (end_idx - i) * avg_time / 3600;

        fprintf( ...
            'OK | %.1f sec | ETA %.2f h\n', ...
            elapsed, ...
            eta_hour);

    catch ME

        fprintf( ...
            'FAILED %d : %s\n', ...
            i, ...
            ME.message);

        try
            ModelUtil.clear;
        catch
        end

    end

end

fprintf('\nFinished.\n');

exit

end
