#!/usr/bin/env python3

import h5py
import sys
import pickle
import numpy as np

EPS = 1e-15

NORDER = 9

weakFDFlag = True
weakString = ""
if weakFDFlag:
    weakString = "_weakFD"

initialFlag = False
pTdiffFlag = True
etadiffFlag = True

kinematicCutsDict = {
    "STAR_eta_-0p5_0p5": {
        "pTmin": 0.2,
        "pTmax": 2,
        "etamin": -0.5,
        "etamax": 0.5
    },
    "STAR_eta_-1_-0p5": {
        "pTmin": 0.2,
        "pTmax": 2,
        "etamin": -1,
        "etamax": -0.5
    },
    "STAR_eta_0p5_1": {
        "pTmin": 0.2,
        "pTmax": 2,
        "etamin": 0.5,
        "etamax": 1
    },
    "STAR_eta_-1_1": {
        "pTmin": 0.2,
        "pTmax": 2,
        "etamin": -1,
        "etamax": 1
    },
}

pidList = [('ch', '9999'), ('pi+', '211'), ('pi-', '-211'), ('K+', '321'),
           ('K-', '-321'), ('p', '2212'), ('pbar', '-2212')]

LHCetaRangeList = [
    '-0.4_0.4', '-0.5_0.5', '-0.8_-0.4', '-2.4_-0.5', '-2.5_-0.5', '-3.7_-1.7',
    '-4.9_-3.1', '-5.1_-2.8', '0.4_0.8', '0.5_2.4', '0.5_2.5', '1.7_3.7',
    '2.8_5.1', '3.1_4.9', '2.8_5.1'
]
RHICetaRangeList = ['-0.5_0.5', '-1_-0.5', '-3.9_-3.1', '0.5_1', '3.1_3.9']


def help_message():
    print("Usage: {0} database_file".format(sys.argv[0]))
    exit(0)


def calcualte_inte_Vn_pT(pT_low, pT_high, data):
    """
        this function calculates the pT-integrated vn in a
        given pT range (pT_low, pT_high) for every event in the data
    """
    npT = 50
    pT_inte_array = np.linspace(pT_low, pT_high, npT)
    dpT = pT_inte_array[1] - pT_inte_array[0]
    dN_event = data[:, 1]
    totalN_event = data[:, -1]
    pT_event = data[:, 0]
    dN_interp = np.exp(
        np.interp(pT_inte_array, pT_event, np.log(dN_event + 1e-30)))
    totalN_interp = np.exp(
        np.interp(pT_inte_array, pT_event, np.log(totalN_event + 1e-30)))
    N = 2.*np.pi*np.sum(dN_interp*pT_inte_array)*dpT
    totalN = np.sum(totalN_interp)*dpT/(pT_event[1] - pT_event[0])
    meanpT = (np.sum(dN_interp*pT_inte_array**2.)
              /np.sum(dN_interp*pT_inte_array))
    temp_vn_array = [N, meanpT]
    for iorder in range(1, NORDER + 1):
        vn_real_event = data[:, 2*iorder]
        vn_imag_event = data[:, 2*iorder + 1]
        vn_real_interp = np.interp(pT_inte_array, pT_event, vn_real_event)
        vn_imag_interp = np.interp(pT_inte_array, pT_event, vn_imag_event)
        Vn_real_inte = (np.sum(vn_real_interp*dN_interp*pT_inte_array)
                        /np.sum(dN_interp*pT_inte_array))
        Vn_imag_inte = (np.sum(vn_imag_interp*dN_interp*pT_inte_array)
                        /np.sum(dN_interp*pT_inte_array))
        temp_vn_array.append(Vn_real_inte + 1j*Vn_imag_inte)
    temp_vn_array.append(totalN)
    return temp_vn_array


def calcualte_inte_Vn_eta(etaMin, etaMax, data, vnFlag=True):
    """
        this function calculates the eta-integrated vn in a
        given eta range (etaMin, etaMax) for every event in the data
    """
    nEta = 50
    eta_inte_array = np.linspace(etaMin, etaMax, nEta)
    deta = eta_inte_array[1] - eta_inte_array[0]
    dN_event = data[:, 1]
    ET_event = data[:, -2]
    totalN_event = data[:, -1]
    eta_event = data[:, 0]
    dN_interp = np.exp(
        np.interp(eta_inte_array, eta_event, np.log(dN_event + 1e-30)))
    totalN_interp = np.exp(
        np.interp(eta_inte_array, eta_event, np.log(totalN_event + 1e-30)))
    ET_interp = np.exp(
        np.interp(eta_inte_array, eta_event, np.log(ET_event + 1e-30)))
    N = np.sum(dN_interp)*deta
    totalN = np.sum(totalN_interp)*deta/(eta_event[1] - eta_event[0])
    ET = np.sum(ET_interp)*deta
    temp_vn_array = [N, ET]
    if vnFlag:
        for iorder in range(1, NORDER + 1):
            vn_real_event = data[:, 2*iorder + 1]
            vn_imag_event = data[:, 2*iorder + 2]
            vn_real_interp = np.interp(eta_inte_array, eta_event, vn_real_event)
            vn_imag_interp = np.interp(eta_inte_array, eta_event, vn_imag_event)
            Vn_real_inte = np.sum(vn_real_interp*dN_interp)/np.sum(dN_interp)
            Vn_imag_inte = np.sum(vn_imag_interp*dN_interp)/np.sum(dN_interp)
            temp_vn_array.append(Vn_real_inte + 1j*Vn_imag_inte)
        temp_vn_array.append(totalN)
    return temp_vn_array


def calcualte_inte_Vn_pTeta(pTMin, pTMax, etaMin, etaMax, data, Nevents):
    """
        this function calculates the pT and eta-integrated vn in a
        given pT range (pTMin, pTMax) and eta range (etaMin, etaMax)
        for every event in the data
    """
    npT = 20
    nEta = 71
    pTArr = np.linspace(0, 3.8, npT)
    dpT = pTArr[1] - pTArr[0]
    pTMinIdx = int((pTMin - 0.)/dpT)
    pTMaxIdx = min(npT, int((pTMax - 0.)/dpT) + 1)
    etaArr = np.linspace(-7, 7, nEta)
    deta = etaArr[1] - etaArr[0]
    etaMinIdx = max(0, int((etaMin - etaArr[0])/deta))
    etaMaxIdx = min(nEta, int((etaMax - etaArr[0])/deta) + 1)

    pT_event = data[:, 1].reshape(nEta, npT)
    dN_event = data[:, 2].reshape(nEta, npT)
    N = np.sum(dN_event[etaMinIdx:etaMaxIdx, pTMinIdx:pTMaxIdx])
    meanpT = (np.sum(pT_event[etaMinIdx:etaMaxIdx, pTMinIdx:pTMaxIdx]
                     *dN_event[etaMinIdx:etaMaxIdx, pTMinIdx:pTMaxIdx])/N)
    totalN = N*Nevents
    temp_vn_array = [N, meanpT]
    for iorder in range(1, NORDER + 1):
        Qn_real_event = data[:, 2*iorder + 2].reshape(nEta, npT)
        Qn_imag_event = data[:, 2*iorder + 3].reshape(nEta, npT)
        Vn_real_inte = (
            np.sum(Qn_real_event[etaMinIdx:etaMaxIdx, pTMinIdx:pTMaxIdx])/N)
        Vn_imag_inte = (
            np.sum(Qn_imag_event[etaMinIdx:etaMaxIdx, pTMinIdx:pTMaxIdx])/N)
        temp_vn_array.append(Vn_real_inte + 1j*Vn_imag_inte)
    temp_vn_array.append(totalN)
    return temp_vn_array


def calcualte_inte_Vneta_pTeta(pTMin: float, pTMax: float, data, Nevents: int):
    """
        this function calculates the pT-integrated vn(eta) in a
        given pT range (pTMin, pTMax) for every event in the data
    """
    npT = 20
    nEta = 71
    pTArr = np.linspace(0, 3.8, npT)
    dpT = pTArr[1] - pTArr[0]
    pTMinIdx = int((pTMin - 0.)/dpT)
    pTMaxIdx = min(npT, int((pTMax - 0.)/dpT) + 1)
    etaArr = np.linspace(-7, 7, nEta)
    deta = etaArr[1] - etaArr[0]

    pT_event = data[:, 1].reshape(nEta, npT)
    dN_event = data[:, 2].reshape(nEta, npT)
    N = np.sum(dN_event[:, pTMinIdx:pTMaxIdx], axis=1) + EPS
    meanpT = (np.sum(
        pT_event[:, pTMinIdx:pTMaxIdx]*dN_event[:, pTMinIdx:pTMaxIdx], axis=1)
              /N)
    totalN = N*Nevents
    temp_vn_array = [N, meanpT]  # dN/deta, <pT>(eta)
    for iorder in range(1, NORDER + 1):
        Qn_real_event = data[:, 2*iorder + 2].reshape(nEta, npT)
        Qn_imag_event = data[:, 2*iorder + 3].reshape(nEta, npT)
        Vn_real_inte = (np.sum(Qn_real_event[:, pTMinIdx:pTMaxIdx], axis=1)/N)
        Vn_imag_inte = (np.sum(Qn_imag_event[:, pTMinIdx:pTMaxIdx], axis=1)/N)
        temp_vn_array.append(Vn_real_inte + 1j*Vn_imag_inte)  # Vn(eta)
    temp_vn_array.append(totalN)
    return temp_vn_array


def calcualte_yield_and_meanpT(pT_low, pT_high, data):
    """
        this function calculates the pT-integrated particle yield and mean pT
        given pT range (pT_low, pT_high) for every event in the data
    """
    npT = 50
    pT_inte_array = np.linspace(pT_low, pT_high, npT)
    dpT = pT_inte_array[1] - pT_inte_array[0]
    dN_event = data[:, 1]
    pT_event = data[:, 0]
    dN_interp = np.exp(
        np.interp(pT_inte_array, pT_event, np.log(dN_event + 1e-30)))
    N = 2.*np.pi*np.sum(dN_interp*pT_inte_array)*dpT
    meanpT = (np.sum(dN_interp*pT_inte_array**2.)
              /np.sum(dN_interp*pT_inte_array))
    res_array = [N, meanpT]
    return res_array


try:
    database_file = str(sys.argv[1])
except IndexError:
    help_message()

h5_data = h5py.File(database_file, "r")
eventList = list(h5_data.keys())

outdata = {}

for ievent, event_i in enumerate(eventList):
    if ievent % 100 == 0:
        print("fetching event: {0} from the database {1} ...".format(
            event_i, database_file))
    eventGroup = h5_data.get(event_i)
    outdata[event_i] = {}
    vn_filename = f"particle_9999_vndata_diff_eta_-0.5_0.5{weakString}.dat"
    vn_data = np.nan_to_num(eventGroup.get(vn_filename))
    dN_vector = calcualte_yield_and_meanpT(0.0, 3.0, vn_data)
    outdata[event_i]["Nch"] = dN_vector[0]
    outdata[event_i]["mean_pT_ch"] = dN_vector[1]

    # compute dET/deta
    vn_filename = f"particle_99999_dNdeta_pT_0_4{weakString}.dat"
    vn_data = np.nan_to_num(eventGroup.get(vn_filename))
    dN_vector = calcualte_inte_Vn_eta(-0.5, 0.5, vn_data, vnFlag=False)
    outdata[event_i]["ET"] = dN_vector[1]

    if initialFlag:
        # initial eccentricity
        ecc_filename = "eccentricities_evo_ed_tau_INITIAL.dat"
        eccn_data = np.nan_to_num(eventGroup.get(ecc_filename))
        outdata[event_i]["ecc_n"] = eccn_data[2:]

    # identified particle yields and mean pT
    for pidName, pid in pidList[1:]:
        vn_filename = f"particle_{pid}_vndata_diff_y_-0.5_0.5{weakString}.dat"
        vn_data = np.nan_to_num(eventGroup.get(vn_filename))
        dN_vector = calcualte_yield_and_meanpT(0.0, 3.0, vn_data)
        outdata[event_i]["{}_dNdy_meanpT".format(pidName)] = dN_vector

    # charged hadron vn with different kinematic cuts
    vn_filename = f'particle_9999_pTeta_distribution{weakString}.dat'
    vnInte_filename = f'particle_9999_vndata_eta_-0.5_0.5{weakString}.dat'
    for exp_i, expName in enumerate(kinematicCutsDict):
        pTetacut = kinematicCutsDict[expName]
        vn_data = np.nan_to_num(eventGroup.get(vn_filename))
        vnInte_data = np.nan_to_num(eventGroup.get(vnInte_filename))
        N_hadronic_events = vnInte_data[-1, 2]
        Vn_vector = calcualte_inte_Vn_pTeta(pTetacut['pTmin'],
                                            pTetacut['pTmax'],
                                            pTetacut['etamin'],
                                            pTetacut['etamax'], vn_data,
                                            N_hadronic_events)
        outdata[event_i][expName] = np.array(Vn_vector)

    if pTdiffFlag:
        # pT-differential spectra and vn
        for pidName, pid in pidList:
            if pid == "9999":
                vn_filename = (
                    f"particle_9999_vndata_diff_eta_-0.5_0.5{weakString}.dat")
            else:
                vn_filename = (
                    f"particle_{pid}_vndata_diff_y_-0.5_0.5{weakString}.dat")
            vn_data = np.nan_to_num(eventGroup.get(vn_filename))
            # dN/(2pi pT dpT dy)
            outdata[event_i]["{}_sp".format(pidName)] = vn_data[:, 1]
            # v2(pT)
            outdata[event_i]["{}_v2pT".format(pidName)] = (vn_data[:, 4]
                                                           + 1j*vn_data[:, 5])
            # v3(pT)
            outdata[event_i]["{}_v3pT".format(pidName)] = (vn_data[:, 6]
                                                           + 1j*vn_data[:, 7])
            # v4(pT)
            outdata[event_i]["{}_v4pT".format(pidName)] = (vn_data[:, 8]
                                                           + 1j*vn_data[:, 9])
    if etadiffFlag:
        # eta-differential spectra and vn
        vn_filename = f'particle_9999_pTeta_distribution{weakString}.dat'
        vnInte_filename = f'particle_9999_vndata_eta_-0.5_0.5{weakString}.dat'
        vn_data = np.nan_to_num(eventGroup.get(vn_filename))
        vnInte_data = np.nan_to_num(eventGroup.get(vnInte_filename))
        N_hadronic_events = vnInte_data[-1, 2]
        Vn_vector = calcualte_inte_Vneta_pTeta(0.2, 2.0, vn_data,
                                               N_hadronic_events)
        outdata[event_i]["chVneta_pT_0p2_2"] = np.array(Vn_vector)

        vn_filename = f"particle_99999_dNdeta_pT_0_4{weakString}.dat"
        vn_data = np.nan_to_num(eventGroup.get(vn_filename))
        outdata[event_i]["dET/deta"] = vn_data[:, -2]
        outdata[event_i]["etaArr"] = vn_data[:, 0]

print("nev = {}".format(len(eventList)))
with open(f'QnVectors{weakString}.pickle', 'wb') as pf:
    pickle.dump(outdata, pf)

h5_data.close()