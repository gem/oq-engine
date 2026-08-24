function generate_interpolated_reference(author_directory, output_file)
% Generate the normalized, data-only interpolation reference CSV.
% GNU Octave 8.4.0 was used for the committed table.

addpath(author_directory);
codes1 = [0.06, 0.15, 0.6, 1.3, 8, 0.6, 0.06, 0.6, 1.3, 8, ...
          0.06, 0.15];
codes2 = [0.06, 0.15, 0.6, 1.3, 8, 1.3, 0.15, -1, -3, -5, ...
          8, 0.75];
distances = [0, 0, 0, 0, 0, 20, 0, 10, 25, 100, 40, 0];
labels1 = {'SA(0.06)', 'SA(0.15)', 'SA(0.6)', 'SA(1.3)', 'SA(8)', ...
           'SA(0.6)', 'SA(0.06)', 'SA(0.6)', 'SA(1.3)', 'SA(8)', ...
           'SA(0.06)', 'SA(0.15)'};
labels2 = {'SA(0.06)', 'SA(0.15)', 'SA(0.6)', 'SA(1.3)', 'SA(8)', ...
           'SA(1.3)', 'SA(0.15)', 'PGV', 'CAV', 'RSD595', 'SA(8)', ...
           'SA(0.75)'};

file = fopen(output_file, 'w');
fprintf(file, ['imt1,imt2,distance,matlab_rho,variance1,variance2,' ...
               'rho\n']);
for index = 1:numel(distances)
    rho = Du_Ning_SpatialCorrelation_IMs(
        codes1(index), codes2(index), distances(index));
    variance1 = Du_Ning_SpatialCorrelation_IMs(
        codes1(index), codes1(index), 0);
    variance2 = Du_Ning_SpatialCorrelation_IMs(
        codes2(index), codes2(index), 0);
    normalized = rho / sqrt(variance1 * variance2);
    fprintf(file, '%s,%s,%.15g,%.15g,%.15g,%.15g,%.15g\n', ...
            labels1{index}, labels2{index}, distances(index), rho, ...
            variance1, variance2, normalized);
end
fclose(file);
end
