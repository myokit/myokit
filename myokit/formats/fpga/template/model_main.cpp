# include "model.hpp"
# include <iostream>
# include <ostream>

// Current and next step state variables
<?
for var in model.states():
    print(f'float Y_{var.index()};')
for var in model.states():
    print(f'float SV_{var.index()};')
?>
// external stimulus
float pace = 0.0f;

// timing variables
float dt = <?= float(sim_step) ?>f;
float tSim = <?= float(sim_duration) ?>f;
int n_iterations = int(tSim / dt);

// Parameters
<?
for p in parameters:
    print(f'float {e.eq(p.eq())};')   # TODO, Comment
?>
int main(int argc, char *argv[]){
    FILE* fp1;

    fp1 = fopen("result.golden.dat", "w");

    // Time and membrane potential
    float* tArray = (float*)malloc(n_iterations * sizeof(float));
    float* Vm = (float*)malloc(n_iterations * sizeof(float));
    float t = 0;
    float t2 = 0;

<?
for var in model.states():
    print(f'{tab}float Y_{var.index()} = {var.initial_value().eval()}f;')  # TODO, Comment
?>
    for(int i=0; i<n_iterations; i++) {
<?
if event is not None:
    print(f'{tab * 2}pace = (t2 >= {float(event.start())}f && t2 < {float(event.start() + event.duration())}f) ? 1.0f : 0.0f;')
?>
        <?= call ?>;

<?
for var in model.states():
    print(f'{tab * 2}Y_{var.index()} = SV_{var.index()};')
?>
        tArray[i] = t;
        Vm[i] = SV_<?= vm.index() ?>;

        t = t+dt;
<?
if event is not None:
    print(f'{tab * 2}t2 = t2 + dt;')
    print(f'{tab * 2}if(t2 > {float(sim_duration)}f) {{ t2 = t2 - {float(sim_duration)}f; }}')
?>
        fprintf(fp1, "%5.4f\n", Vm[i]);
    }

    fclose(fp1);
    free(tArray);
    free(Vm);

    // Uncomment only when importing in VITIS
/*     // Compare the results file with the golden results
    retval = system("diff --brief -w result.dat result.golden.dat");
    if (retval != 0) {
        std::cout << "Test failed  !!!" << std::endl;
        retval=1;
    } else {
        std::cout << "Test passed !" << std::endl;
    }

    // Return 0 if the test
    return 0;//retval;
 */
}
