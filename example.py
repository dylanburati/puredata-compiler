from puredata_compiler import Patch, write_file

# pylint: disable=unused-variable


def envelope() -> Patch:
    """Subpatch for generating an ADSR envelope"""
    patch = Patch()
    obj, msg = patch.get_creators('obj, msg')

    inlet = obj('inlet')
    # 0:volume 1-4:ADSR[ms,ms,scalar,ms]
    env_unpacker = obj('unpack 0 0 0 0 0', inlet[0])

    attack_if = obj('moses 1e-12', env_unpacker[0])
    nonzero_volume = obj('f', attack_if[1], new_row=2)
    if True:  # branch for volume > 0
        attack_trig = obj('t b b', nonzero_volume[0], new_row=0)
        prerelease_params = msg('1', attack_trig[1], new_row=0)
        sustain_sqrt = obj('expr sqrt($f2)', attack_trig[0], env_unpacker[3])
        attack_prep = obj(
            'pack 0 0 0', sustain_sqrt[0], env_unpacker[1], env_unpacker[2])
        attack_params = msg('0, 1 $2, $1 $3 $2', attack_prep[0])
        attack_env = obj('vline~', attack_params[0])
    if True:  # branch for volume == 0
        release_trig = obj('t b', attack_if[0], x_pos=325, y_pos=125)
        release = obj('f', release_trig[0], env_unpacker[4], new_row=0)
        release_params = msg('0 $1', release[0])
        release_env = obj('vline~', (prerelease_params[0], release_params[0]))

    full_env = obj('*~', attack_env[0], release_env[0], x_pos=125, y_pos=250)
    full_env = obj('*~', full_env[0], nonzero_volume[0])
    full_env = obj('*~', full_env[0], full_env[0])
    obj('outlet~', full_env[0])

    return patch


def example() -> Patch:
    """Subpatch for playing a section from a given wavetable"""
    patch = Patch()
    obj, msg, subpatch = patch.get_creators('obj, msg, subpatch')

    loadbang = obj('loadbang')
    msg('pd dsp 1', loadbang[0])
    note_on = msg('1; note 440 0.8  80 0 1.0 320', new_row=2)
    note_off = msg('1; note 440 0.0  80 0 1.0 320')

    inlet = obj('r note', x_pos=425, y_pos=25)
    # 0:frequency 1:volume 2-5:ADSR[ms,ms,scalar,ms]
    note_unpacker = obj('unpack 0 0  0 0 0 0', inlet[0])
    note_unpacker_trig = obj('t b f', note_unpacker[0])

    allow_freq_change_test = obj('f', note_unpacker_trig[0], note_unpacker[1])
    allow_freq_change_if = obj('moses 1e-12', allow_freq_change_test[0])
    osc_params = obj('expr $f2', allow_freq_change_if[1], note_unpacker_trig[1])
    osc = obj('osc~', osc_params[0], new_row=2)
    envelope_params = obj('pack 0 0 0 0 0', note_unpacker[1], note_unpacker[2],
                          note_unpacker[3], note_unpacker[4], note_unpacker[5],
                          x_pos=550, y_pos=125)
    pd_envelope = subpatch('envelope', envelope(), envelope_params[0])

    output = obj('*~', osc[0], pd_envelope[0])
    obj('dac~', output[0], output[0])

    return patch


if __name__ == "__main__":
    pd_example = example()
    write_file('pd_example.pd', str(pd_example))
