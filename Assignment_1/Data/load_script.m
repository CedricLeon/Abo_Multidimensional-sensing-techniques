inputFilename  = 'Stairs.mat';
outputFilename = 'Stairs.csv';
% Fast-walk-straight_8steps.mat // Slow-walk-in-circle_8steps.mat // Stairs

load(inputFilename);
temp = [[1: length(Acceleration.Timestamp)]', Acceleration{:, :}];
csvwrite(outputFilename, temp);
