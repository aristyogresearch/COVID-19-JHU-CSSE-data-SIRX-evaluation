import numpy as np
from scipy.integrate import ode
from lmfit import minimize, Parameters

class SIRXConfirmedModel:

    def __init__(self):
        self.initial_conditions = None


    # set equation of motion for SIRX dynaics
    def dxdt(self,t,y,eta,rho,kappa,kappa0):

        S = y[0]
        I = y[1]
        X = y[2]
        H = y[3]
        R = y[4]
     
        dy = np.zeros(5)
        dy[0] = -eta*S*I - kappa0*S
        dy[1] = +eta*S*I - rho*I - kappa*I - kappa0*I
        dy[2] = +kappa*I + kappa0*I
        dy[3] = +kappa0*S
        dy[4] = +rho*I


        return dy

    def set_initial_conditions(self,SIRX0):
        self.initial_conditions = SIRX0.copy()

    def SIRX(self,t, y0, eta, rho, kappa,kappa0, N, I0_factor):

        if self.initial_conditions is not None:
            y0 = self.initial_conditions
        else:
            X0 = y0/N
            I0 = X0 * I0_factor
            S0 = 1-X0-I0
            y0 = np.array([S0, I0, X0, 0.0, 0.0])

        t0 = t[0]

        t = t[1:]

        r = ode(self.dxdt)

        # Runge-Kutta with step size control
        r.set_integrator('dopri5')

        # set initial values
        r.set_initial_value(y0,t0)

        # set transmission rate and recovery rate
        r.set_f_params(eta,rho,kappa,kappa0)

        result = np.zeros((5,len(t)+1))
        result[:,0] = y0

        # loop through all demanded time points
        for it, t_ in enumerate(t):

            # get result of ODE integration
            y = r.integrate(t_)

            # write result to result vector
            result[:,it+1] = y

        return result

    def residual(self,params, x, data):

        R0 = params['R0']
        rho = params['rho']
        eta = R0*rho
        kappa = params['kappa']
        kappa0 = params['kappa0']
        I0_factor = params['I0_factor']
        #N = 10**params['log10N']
        N = params['N']

        result = self.SIRX(x, data[0], eta, rho, kappa, kappa0, N, I0_factor)
        X = result[2,:]

        residual = X*N - data

        return residual
    
    def fit(self,t, data,maxfev=100000,params=None,N=None,Nmax=None,method='Nelder'):

        if params is None:
            params = Parameters()
            R0 = 3.07
            rho = 0.38
            eta = R0*rho
            params.add('R0',value=R0,vary=False)
            params.add('eta',value=eta, vary=False) # Michi: I added this line!!! Plz check!
            params.add('rho',value=rho, vary=False)
            params.add('kappa',value=rho,min=0)        
            params.add('kappa0',value=rho/2,min=0)
            params.add('I0_factor',value=10,min=0.001,vary=self.initial_conditions is None)
            varyN = N is None
            if varyN:
                N = 1e7
            if Nmax is None:
                Nmax=115000000
            params.add('N',value=N,min=1000,max=Nmax,vary=varyN)

        out = minimize(self.residual, params, args=(t, data, ),
                       #maxfev=maxfev,
                       method=method,
                )
        return out

