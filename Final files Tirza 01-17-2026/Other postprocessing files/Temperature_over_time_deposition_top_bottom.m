clear; clc;
close all;

% ---------------------- USER SETTINGS ---------------------------
csv_folder_path = "C:\Users\Tirza\Documents\Abaq_finalcleanXS\";                     % path to folder where csv files are stored
point_names_bottom = ["P_-15_8_132", "P_0_8_152", "P_-14_8_133"];                  % define name of points which you also used in the python file
point_names_top = ["P_-15_8_5_132_nodenr_input", "P_0_8_5_152_nodenr_input", "P_-14_8_5_133_nodenr_input"];                  % define name of points which you also used in the python file
top_points_deposited = [39, 461, 39];       % frame in which node is deposited for each point. you find this by looking at NT11 where the temperature goed from 300 to a higher value and a big increase in the stresses
number_of_steps = 6;

for i = 1:length(point_names_bottom)
    bottom_point = point_names_bottom(i);
    top_point = point_names_top(i);
    top_point_deposited = top_points_deposited(i);

    %% Extracting data bottom point

    % NT11 data
    csv_path_bottom = csv_folder_path + "NT11_over_time_XS_" + bottom_point + ".csv";
    opts = detectImportOptions(csv_path_bottom);
    opts.DataLines = [6 Inf];                                       % import data from row 6-inf
    dataTable = readtable(csv_path_bottom, opts); 
    NT11_data_bottom = table2array(dataTable(:, 5:end)); 

    % Frame data
    meta = readcell(csv_path_bottom, 'Delimiter', ',', 'Range', '1:1');
    raw_frames = meta(2:(number_of_steps + 1));   % extract only the needed cells
    raw_frames = string(raw_frames);              % convert to string so strrep works
    raw_frames = strrep(raw_frames, '"', '');     % remove double quotes
    frames_per_step = double(raw_frames);         % convert to numbers
    frames_per_step_cumsum = cumsum(frames_per_step);       % cumsum frames over steps

    % Point data
    meta_point = readcell(csv_path_bottom, 'Range', '2:2');
    P_string_raw = meta_point{2}; 
    P_string_cleaned = strrep(P_string_raw, ',"', '');              % clean the string to get clean coordinates
    P_bottom = strrep(P_string_cleaned, '"', '');

    % Time data
    meta_time = readmatrix(csv_path_bottom, 'Range', '3:3');
    time = meta_time(5:end);

    offset = 0;                                                     % fix time reset
    start_index = 1;
    
    for s = 1:length(frames_per_step)
        end_index = frames_per_step_cumsum(s);
        time(start_index:end_index) = time(start_index:end_index) + offset;
        offset = time(end_index);
        start_index = end_index + 1; 
    end

    % Extracting deposition data only
    frame_deposition_start = frames_per_step_cumsum(2) + 1;
    frame_deposition_end = frames_per_step_cumsum(3);

    NT11_data_bottom_deposition = NT11_data_bottom(:, frame_deposition_start:frame_deposition_end);
    time_bottom_deposition = time(:, frame_deposition_start:frame_deposition_end);

    %% Extracting data top point
    csv_path_top = csv_folder_path + "NT11_over_time_XS_" + top_point + ".csv";
    opts = detectImportOptions(csv_path_top);
    opts.DataLines = [6 Inf];                                       % import data from row 6-inf
    dataTable = readtable(csv_path_top, opts); 
    NT11_data_top = table2array(dataTable(:, 5:end)); 

    % Point data
    meta_point = readcell(csv_path_top, 'Range', '2:2');
    P_string_raw = meta_point{2}; 
    P_string_cleaned = strrep(P_string_raw, ',"', '');              % clean the string to get clean coordinates
    P_top = strrep(P_string_cleaned, '"', '');

    % Extracting deposition data only
    NT11_data_top_deposition = NT11_data_top(:, top_point_deposited+1:frame_deposition_end);
    time_top_deposition = time(:, top_point_deposited+1:frame_deposition_end);


    %% Plotting NT11 for top and bottom
    point_names_legend = [P_bottom, P_top];

    figure;
    hold on
    plot(time_bottom_deposition, NT11_data_bottom_deposition, 'LineWidth', 1.5, 'DisplayName', P_bottom)
    plot(time_top_deposition, NT11_data_top_deposition, 'LineWidth', 1.5, 'DisplayName', P_top)
    hold off
    xlim([time_bottom_deposition(1), time_bottom_deposition(end)])
    xlabel('Time (s)');
    ylabel('Temperature (K)');
    title("Temperature over time for points " + P_bottom + " and " + P_top);
    grid on;
    legend('Location', 'best');
    %savefig("C:\Users\Tirza\Documents\My codes for postprocessing\" + "NT11_points_" + P_bottom + ".fig");
    %saveas(gcf, "C:\Users\Tirza\Documents\My codes for postprocessing\" + "NT11_points_" + P_bottom + ".png");

    %% Plotting NT11 for bottom
    if i == 1
        figure;
        hold on
        plot(time, NT11_data_bottom, 'LineWidth', 1.5)
        xline(time(frames_per_step_cumsum), '--', 'LineWidth', 1);
        hold off
        %xlim([time(1), time(end)])
        xlim([time(frames_per_step_cumsum(2)+1), time(frames_per_step_cumsum(3))])
        xlabel('Time (s)');
        ylabel('Temperature (K)');
        title("Temperature over time for point " + P_bottom);
        grid on;
        %savefig("C:\Users\Tirza\Documents\My codes for postprocessing\" + "NT11_coldspray_point_" + P_bottom + ".fig");
        saveas(gcf, "C:\Users\Tirza\Documents\My codes for postprocessing\" + "NT11_coldspray_point_" + P_bottom + ".png");
    end

end