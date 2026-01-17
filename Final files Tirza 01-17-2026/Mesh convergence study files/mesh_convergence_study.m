clear; clc;
close all;

% ---------------------- USER SETTINGS ---------------------------
csv_folder_paths = ["E:\Tirza\Abaq_finalcleanB\", "E:\Tirza\Abaq_finalcleanS\"];               % path to folders where csv files are stored in same order as mesh_names
mesh_names = ["B", "S"];                                                    % define names of mesh which you also used in the python file
point_names = ["P_-15_8_132", "P_0_8_152", "P_-14_8_133"];                  % define name of points which you also used in the python file
all_fieldoutput = ["NT11", "S11", "Smises"];                                % list all field output values which you want to investigate
threshold_temp = 0.05;                                                      % error threshold for mesh convergence for temperature
threshold_stress = 0.1;                                                     % error threshold for mesh convergence for stress 
number_of_steps = 6;
% ----------------------------------------------------------------

Mises_errors = zeros(length(mesh_names) - 1);

for field_output = 1:length(all_fieldoutput)  

    if all_fieldoutput(field_output) == "NT11"
        threshold = threshold_temp;
    else
        threshold = threshold_stress;
    end

    for point = 1:length(point_names)
        for mesh = 1:length(mesh_names)
            % Load CSV data
            csv_path = csv_folder_paths(mesh) + all_fieldoutput(field_output) + "_over_time_" + mesh_names(mesh) + "_" + point_names(point) + ".csv";
            opts = detectImportOptions(csv_path);
            opts.DataLines = [6 Inf];                                       % import data from row 6-inf
            dataTable = readtable(csv_path, opts); 
            data = table2array(dataTable(:, 2:end)); 

            % Read metadata rows    
            meta = readcell(csv_path, 'Delimiter', ',', 'Range', '1:1');
            raw_frames = meta(2:(number_of_steps + 1));   % extract only the needed cells
            raw_frames = string(raw_frames);              % convert to string so strrep works
            raw_frames = strrep(raw_frames, '"', '');     % remove double quotes
            frames_per_step = double(raw_frames);         % convert to numbers
            frames_per_step_cumsum = cumsum(frames_per_step);       % cumsum frames over steps

            meta_point = readcell(csv_path, 'Range', '2:2');
            P_string_raw = meta_point{2}; 
            P_string_cleaned = strrep(P_string_raw, ',"', '');              % clean the string to get clean coordinates
            P = strrep(P_string_cleaned, '"', '');

            meta_time = readmatrix(csv_path, 'Range', '3:3');
            time = meta_time(4:end);
            
            % Fix time reset per step 
            offset = 0;
            start_index = 1;
            
            for s = 1:length(frames_per_step)
                end_index = frames_per_step_cumsum(s);
            
                % Fix times in this step by adding the cumulative offset
                time(start_index:end_index) = time(start_index:end_index) + offset;
            
                % Update the offset for the next step
                offset = time(end_index);
            
                start_index = end_index + 1; 
            end
            
            % Exract data columns: Node | xp | yp | zp | T0 | T1 | ... | Tn
            xp = data(:,1);
            yp = data(:,2);
            zp = data(:,3);
            T = data(:,4:end);                                              % field output per frame
            nFrames = size(T,2);                                            % number of frames

            if size(T,1) > 1
                error("Multiple points were found in selection box. This should not happen.")
            end

            % Create empty matrices to store values
            if mesh == 1
                mesh_comparison = zeros(length(mesh_names), nFrames);
                xp_mesh_comparison = zeros(length(mesh_names), size(xp, 1));
                yp_mesh_comparison = zeros(length(mesh_names), size(yp, 1));
                zp_mesh_comparison = zeros(length(mesh_names), size(zp, 1));
                mesh_comparison_errors = zeros(length(mesh_names) - 1, nFrames);
                errors_below_threshold = zeros(length(mesh_names) - 1, nFrames);
                mesh_converged = zeros(length(mesh_names) - 1, 1);
            end

            % Store values
            mesh_comparison(mesh, :) = T;
            xp_mesh_comparison(mesh) = xp;
            yp_mesh_comparison(mesh) = yp;
            zp_mesh_comparison(mesh) = zp;

            % When there are two meshes stored in the mesh_comparison variable, the errors can be calculated
            if mesh > 1
                mesh_comparison_errors(mesh - 1, :) = calculatingErrors(mesh_comparison, mesh);
                errors_below_threshold(mesh - 1, :) = mesh_comparison_errors(mesh - 1, :) < threshold;
                mesh_converged(mesh - 1) = all(errors_below_threshold(mesh - 1, :));

                % Path plot of errors over time
                errors_plot = mesh_comparison_errors(mesh - 1, :);
                figure;
                plot(time, errors_plot, 'LineWidth', 1.5);
                hold on
                yline(threshold, 'k--', 'LineWidth', 1.5);
                hold off
                xlabel('Time (s)');
                ylabel('Absolute relative error (-)');
                title("Absolute relative error over time for " + all_fieldoutput(field_output) + " for point " + P + " for mesh size " + mesh_names(mesh - 1));
                grid on;
            end
        end % end of mesh loop

        % Print important output
            fprintf('\nField output considered: %s\n', all_fieldoutput(field_output))
            fprintf('Point considered (x,y,z): P = %s\n', P)
            for mesh_error = 1:size(mesh_comparison_errors, 1)
                mean_error = mean(mesh_comparison_errors(mesh_error, :));
                fprintf('Average error across all frames: %.2f\n', mean_error);
                if field_output == length(all_fieldoutput)
                    Mises_errors(mesh_error) = Mises_errors(mesh_error) + mean_error;
                end
            end
            fprintf('Mesh converged (1 = true, 0 = False):\n%d\n', mesh_converged);

    end % end of point loop
end % end of field output loop

for Mises_errors_i = 1:(length(mesh_names) - 1)
    fprintf('\nAverage error von Mises stress across all frames and all points: %.2f\n', (Mises_errors(Mises_errors_i)/length(point_names)));
end

% Function to calculate errors
function errors = calculatingErrors(mesh_comparison, mesh)
    V_coarser = mesh_comparison(mesh - 1, :);
    V_finer = mesh_comparison(mesh, :);

    difference = V_coarser - V_finer;
    errors = abs(difference ./ V_finer);
end