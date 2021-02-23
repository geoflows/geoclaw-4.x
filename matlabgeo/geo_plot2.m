
% Called from plotframe2 if
%   PlotType == 13 (colored surface plot of topography and/or fluid)
% Set
%   PlotTopo == 1 to plot topography, 0 to suppress
%   PlotFlow == 1 to plot flow, 0 to suppress

if ~exist('PlotTopo')
  PlotTopo = 1;
  disp('*** setting PlotTopo = 1.  Set to 0 to suppress topography')
  end
if ~exist('PlotFlow')
  PlotFlow = 1;
  disp('*** setting PlotFlow = 1.  Set to 0 to suppress plotting flow')
end

meqnS = size(data);
meqn = meqnS(2);
neta = meqn;
h = reshape(data(:,1),mx,my);                % depth
hu = reshape(data(:,2),mx,my);               % momentum
hv = reshape(data(:,3),mx,my);
eta = reshape(data(:,neta),mx,my);              % surface
topo = reshape(data(:,neta)-data(:,1),mx,my);   % topography

if PlotType == 13

    [X,Y]=ndgrid(xedge,yedge);   % (mx+1) by (my+1) arrays

    % augmented versions for surface commands, which ignore last row and col:
    %h2 = nan(mx+1,my+1);     h2(1:mx,1:my) = h;
    %hu2 = nan(mx+1,my+1);    hu2(1:mx,1:my) = hu;
    %hv2 = nan(mx+1,my+1);    hv2(1:mx,1:my) = hv;
    %eta2 = nan(mx+1,my+1);   eta2(1:mx,1:my) = eta;
    %topo2 = nan(mx+1,my+1);  topo2(1:mx,1:my) = topo;

    h2 = h;   h2(:,my+1) = h2(:,my);   h2(mx+1,:) = h2(mx,:);
    hu2 = hu;   hu2(:,my+1) = hu2(:,my);   hu2(mx+1,:) = hu2(mx,:);
    hv2 = hv;   hv2(:,my+1) = hv2(:,my);   hv2(mx+1,:) = hv2(mx,:);
    eta2 = eta;   eta2(:,my+1) = eta2(:,my);   eta2(mx+1,:) = eta2(mx,:);
    topo2 = topo;   topo2(:,my+1) = topo2(:,my);   topo2(mx+1,:) = topo2(mx,:);


    if mq==1
        eta2color = h2;
    elseif ((mq==2)&(plotspeed==0))
        eta2color = hu2./h2;
    elseif ((mq==3)&(plotspeed==0))
        eta2color = hv2./h2;
    elseif mq==4
        eta2color = eta2;
    elseif ((mq==2|mq==3)&(plotspeed==1))
        hdiv = max(h2,1.e-3);
        eta2color = sqrt((hu2./hdiv).^2 + (hv2./hdiv).^2);
    end


    if PlotTopo
      % plot topography:
      geo_plot_topo
      end

    if PlotFlow
      % plot surface of flow:
      geo_plot_surface
      end

    view(2)  % top view
    axis tight

end

if PlotType == 12

    [X,Y]=ndgrid(x,y);% (mx) by (my) arrays
    [Xe,Ye]=ndgrid(xedge,yedge);

    % augmented versions for surface commands, which ignore last row and col:
    %h2 = nan(mx+1,my+1);     h2(1:mx,1:my) = h;
    %hu2 = nan(mx+1,my+1);    hu2(1:mx,1:my) = hu;
    %hv2 = nan(mx+1,my+1);    hv2(1:mx,1:my) = hv;
    %eta2 = nan(mx+1,my+1);   eta2(1:mx,1:my) = eta;
    %topo2 = nan(mx+1,my+1);  topo2(1:mx,1:my) = topo;

    h2 = h; %  h2(:,my+1) = h2(:,my);   h2(mx+1,:) = h2(mx,:);
    hu2 = hu;%   hu2(:,my+1) = hu2(:,my);   hu2(mx+1,:) = hu2(mx,:);
    hv2 = hv; %  hv2(:,my+1) = hv2(:,my);   hv2(mx+1,:) = hv2(mx,:);
    eta2 = eta;%   eta2(:,my+1) = eta2(:,my);   eta2(mx+1,:) = eta2(mx,:);
    topo2 = topo;%   topo2(:,my+1) = topo2(:,my);   topo2(mx+1,:) = topo2(mx,:);


    if mq==1
        eta2color = h2;
    elseif mq==2
        eta2color = hu2./h2;
    elseif mq==3
        eta2color = hv2./h2;
    elseif mq==4
        eta2color = eta2;
    end


    if PlotTopo
      % plot topography:
      geo_plot_topo_pcolor
      end

    if PlotFlow
      % plot surface of flow:
      geo_plot_surface_pcolor
      end

    view(2)  % top view
    axis tight

end




%----------------------------------


