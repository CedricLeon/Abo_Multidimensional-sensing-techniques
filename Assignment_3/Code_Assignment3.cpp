// --- LDR Pins ---
int LDR1Pin = A0;
int LDR2Pin = A1;
int LDR3Pin = A2;
int LDR4Pin = A3;

// Global variables
int const nbSensors = 4;
int const LDRBufferWidth = 10;

// --- LDR Values ---
int LDRValues[nbSensors][LDRBufferWidth] = {};
int index = 0; // index of the circular array 'LDRValues'
float indivStats[nbSensors][2] = {}; // Matrix with 'nbSensors' columns and 2 lines (first for average, second for variance)

// ---------- Setup Function ----------
// Sets serial port for communication
void setup() { Serial.begin(9600); }

// ---------- Faulty sensor detection Function ----------
// This function takes as inputs: the global average and variance over the last loop and the individual statistics over the last 'LDRBufferWidth' samples
// If one sensor is detected as "defected" it returns its index (from 0 to 'nbSensors-1')
// We consider defected a sensor which individual mean is far from the global mean (absolute distance > 150) and if the global variance is huge (> 40.000). We compute each absolute distances and then take the biggest (to avoid returning the first distance over 150)
// This function will only be called when we reach the 'LDRBufferWidth' index (i.e. end of the sliding window)
int detectFaultySensor(float gAvg, float gVar, float indivStats[nbSensors][2]);

// ---------- Main Loop ----------
void loop()
{
  Serial.print("Index = ");
  Serial.println(index);

  // --- Read and store each sensor value ---
  LDRValues[0][index] = analogRead(LDR1Pin);
  LDRValues[1][index] = analogRead(LDR2Pin);
  LDRValues[2][index] = analogRead(LDR3Pin);
  LDRValues[3][index] = analogRead(LDR4Pin);

  // --- Print each value (DEBUG purpose) ---
  Serial.print("   Values: ");
  for(int i = 0; i < nbSensors-1; i++)
  {
    Serial.print(LDRValues[i][index]);
    Serial.print(", ");
  }
  Serial.print(LDRValues[nbSensors-1][index]);
  Serial.println(".");

  // ---------- Compute statistics ----------
  float avg = 0;
  float var = 0;
  // --- Average Computation ---
  for(int i = 0; i < nbSensors; i++)
    avg += LDRValues[i][index];
  avg /= nbSensors;
  // --- Variance Computation ---
  for(int i = 0; i < nbSensors; i++)
    var += (LDRValues[i][index] - avg)*(LDRValues[i][index] - avg);
  var /= nbSensors;

  // --- Print (DEBUG purpose) ---
  Serial.print("   Global avg = ");
  Serial.print(avg);
  Serial.print(" and var = ");
  Serial.println(var);

  // --- Index update and if needed individual stats computation ---
  //index = (index == LDRBufferWidth-1) ? 0 : index+1;
  if(index == LDRBufferWidth-1)
  {
    // For each sensor
    for(int i = 0; i < nbSensors; i++)
    {
      // Compute each individual average
      float indiv_avg = 0;
      for(int j = 0; j < LDRBufferWidth; j++)
        indiv_avg += LDRValues[i][j];
      indiv_avg /= LDRBufferWidth;

      // Compute each individual variance
      float indiv_var = 0;
      for(int j = 0; j < LDRBufferWidth; j++)
        indiv_var += (LDRValues[i][j] - indiv_avg)*(LDRValues[i][j] - indiv_avg);
      indiv_var /= LDRBufferWidth;

      // Update indivStats
      indivStats[i][0] = indiv_avg;
      indivStats[i][1] = indiv_var;

      // Debug printing
      Serial.print("LDR ");
      Serial.print(i);
      Serial.print(": avg = ");
      Serial.print(indiv_avg);
      Serial.print(", var = ");
      Serial.println(indiv_var);
    }

    // Defect detection (Check only every 'LDRBufferWidth' samples)
    int faultySensor = detectFaultySensor(avg, var, indivStats);
    if(faultySensor == -1)
      Serial.println("No faulty sensor detected.");
    else
    {
      Serial.print("/!\\ Faulty sensor detected: LDR ");
      Serial.println(faultySensor);
    }

    // Reset index
    index = 0;
  }else
  {
    index ++;
  }

  // --- Loop delay ---
  Serial.println();
  delay(500);
}


int detectFaultySensor(float gAvg, float gVar, float indivStats[nbSensors][2])
{
  // Check that the global variance is huge
  if(gVar < 40000)
    return -1;

  float globalAvgDistances[nbSensors] = {};

  // For each sensor compute
  for(int i = 0; i < nbSensors; i++)
    globalAvgDistances[i] = abs(indivStats[i][0] - gAvg);

  // Look for the biggest distance
  float max = 0;
  int maxIndex = -1;
  for(int i = 0; i < nbSensors; i++)
  {
    if(globalAvgDistances[i] > max)
    {
      max = globalAvgDistances[i];
      maxIndex = i;
    }
  }

  if(max > 150)
    return maxIndex;
  return -1;
}
