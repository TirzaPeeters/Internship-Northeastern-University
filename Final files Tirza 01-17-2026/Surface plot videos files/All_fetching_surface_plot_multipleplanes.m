clear; clc;
close all;

% ---------------------- USER SETTINGS ---------------------------
csv_folder_path = "C:\Users\Tirza\Documents\Abq_XS1_10trk\";                     % path to folder where csv files are stored
surface_names = ["vertical_x0", "vertical_x-5", "horizontal_y8", "horizontal_y8_5"];                  % define names of surface which you also used in the python file
all_fieldoutput = ["NT11", "S11", "S22", "S33", "Smises"];     % list all field output values which you want to plot
step_names = {'HotplateSS', 'PreHeating', 'Deposition', 'Cooling1', 'ReleaseFixtures', 'Cooling2'};
z_text = ["NT11 [K]", "\sigma_{11} [kPa]", "\sigma_{22} [kPa]", "\sigma_{33} [kPa]", "\sigma_{mises} [kPa]"];    % Define labels for z-axis in plot
% ----------------------------------------------------------------

for plane=1:length(surface_names)
    surface_name = surface_names(plane);

    start_time = tic;               % start timer
    
    for field_output = 1:length(all_fieldoutput)  
        % Load CSV data
        csv_path = csv_folder_path + all_fieldoutput(field_output) + "_over_time_" + surface_name + "_surface.csv";
        opts = detectImportOptions(csv_path);
        opts.DataLines = [6 Inf];                               % import data from row 6-inf
        data = readmatrix(csv_path, opts);
        
        % Read metadata rows
        meta = readmatrix(csv_path, 'Range', '1:1');
        frames_per_step = meta(2:end);
        frames_per_step_cumsum = cumsum(frames_per_step);       % cumsum frames over steps
        
        meta_corners = readcell(csv_path, 'Range', '2:2');
        P1 = str2num(meta_corners{2}); 
        P2 = str2num(meta_corners{3});
        P3 = str2num(meta_corners{4});
        P4 = str2num(meta_corners{5});
        
        meta_time = readmatrix(csv_path, 'Range', '3:3');
        time = meta_time(5:end);
        
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
        xp = data(:,2);
        yp = data(:,3);
        zp = data(:,4);
        T = data(:,5:end);                                      % temperature per frame
        nFrames = size(T,2);                                    % number of frames
        
        % Create grid for surf plot
        res = 50;
        [uq, vq] = ndgrid(linspace(min(xp),max(xp),res), linspace(min(yp),max(yp),res));
        
        figure('Color','w');
        colormap('jet'); 
        shading interp
        
        % Set limits for axis and colormap
        zmin = min(T(:));
        zmax = max(T(:)); 
        z_range = zmax - zmin;
        x_range = max(xp(:)) - min(xp(:));
        y_range = max(yp(:)) - min(yp(:));
        zlim([zmin zmax]);   
        xlim([min(xp) max(xp)]);
        ylim([min(yp) max(yp)]);
        
        colorbar;
        view(3);
        axis manual;
        
        % Create surf plot and video
        videoFile = all_fieldoutput(field_output) + "_over time_" + surface_name + "surface.mp4";        % video file name
        vWriter = VideoWriter(videoFile, 'MPEG-4');
        vWriter.FrameRate = 20;
        open(vWriter);
        
        for i = 1:nFrames
        
            % Determine which step this frame belongs to
            for j = 1:length(frames_per_step_cumsum)
                if i <= frames_per_step_cumsum(j)
                    current_step_name = step_names{j};
                    break;
                end
            end
        
            % Interpolate scattered temperature data to grid
            Tgrid = griddata(xp, yp, T(:,i), uq, vq, 'natural');
        
            % Plot surface
            surf(uq, vq, Tgrid);
            title(sprintf('%s - Frame %d - t = %.2f s', current_step_name, i, time(i)));
            hYlabel = ylabel(sprintf("y' coordinate [mm]\n(distance from P1 towards P4)"));
            hXlabel = xlabel(sprintf("x' coordinate [mm]\n(distance from P1 towards P2)"));
            zlabel(z_text(field_output));
            zlim([zmin zmax]);
            clim([zmin zmax]); 
            colorbar;
        
            % Set position of xlabel
            pos = get(hXlabel, 'Position');
            pos(1) = pos(1) + 0.1*x_range;
            pos(3) = pos(3) + 0.08*z_range;
            set(hXlabel, 'Position', pos);
        
            % Set position of ylabel
            pos = get(hYlabel, 'Position');
            pos(2) = pos(2) + 0.5*y_range;
            pos(1) = pos(1) + 0.1*x_range;
            set(hYlabel, 'Position', pos);
        
            drawnow;
            pause(0.01);                                        % ensure plot and title are fully updated
        
            % Write frame to video
            writeVideo(vWriter, getframe(gcf));
        end
        
        close(vWriter);
        disp(['Movie saved as: ', videoFile]);

    end
    
    fprintf('Corner point P1 (x,y,z) = (%.2f, %.2f, %.2f)\n', P1);
    fprintf('Corner point P2 (x,y,z) = (%.2f, %.2f, %.2f)\n', P2);
    fprintf('Corner point P3 (x,y,z) = (%.2f, %.2f, %.2f)\n', P3);
    fprintf('Corner point P4 (x,y,z) = (%.2f, %.2f, %.2f)\n', P4);

    elapsed_time = toc(start_time);                     % end timer
    fprintf('\nruntime: %.2f', elapsed_time);
   
end