import os,re
from waflib import Task,Errors,Node,TaskGen,Configure

def configure(conf):
	conf.env.AMSDESIGNER = 'amsdesigner'
	if not conf.env.AMSDESIGNER_OPTIONS:
		conf.env.AMSDESIGNER_OPTIONS = [
				'-netlist', 'all',
				'-compile', 'all',
				'-rundir', '.',
				'-ncvlogopt', '-use5x', '-64bit',
			]

	conf.env['CADENCE_SI'] = 'si'

class cdsNetlistTask(Task.Task):

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		run_str = '${AMSDESIGNER} -lib '+self.generator.libname+' -cell '+self.generator.cellname+' -view '+self.generator.viewname+' ${AMSDESIGNER_OPTIONS} '

		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)

class auCdlTask(Task.Task):
	run_str = 'rm -f .running && ${CADENCE_SI} -batch -command netlist'


#	def run(self):
#		split_path = Node.split_path(self.inputs[0].abspath())
#		split_path.reverse()
#		lib = split_path[3]
#		cell = split_path[2]
#		view = split_path[1]
#
#		cmd = 'amsdesigner -lib %s -cell %s -view %s -compile all -netlist all -rundir . -ncvlogopt "-use5x -64bit"' % (lib,cell,view)
#		return self.exec_command(cmd)
#
#	#def runnable_status(self):
#	#    pass

@TaskGen.feature('cds_netlist_sim')
def add_cds_netlist_target(self):
	try:
		cellview = getattr(self,'view','')
		if cellview.find('.') == -1 or cellview.find(':') == -1:
			Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_netlist\'.')
			return
		(self.libname,rest) = cellview.split(".")
		(self.cellname,self.viewname) = rest.split(":")

		config_file = self.path.find_dir(self.env['CDS_LIBS_FLAT'][self.libname])
		if not config_file:
			raise Errors.ConfigurationError('Library '+lib+' in '+selv.env['CDS_LIBS_FLAT'][self.libname]+' not found')
		config_file = config_file.make_node(self.cellname+'/'+self.viewname+'/expand.cfg')
		#if not config_file:
		#	raise Errors.ConfigurationError('Cellview '+self.cellname+':'+self.viewname+' in library '+self.libname+' not found.')

		t = self.create_task('cdsNetlistTask', config_file)
	except ValueError:
		raise Errors.ConfigurationError('For feature "cds_netlist", you need to specify a parameter "toplevel" in the form of lib.cell:view')

@TaskGen.feature('cds_netlist_lvs')
def add_cds_netlist_lvs_target(self):
	m0 = re.search('(\w+).(\w+):(\w+)', self.cellview)
	if m0:
		# the input file of the netlist task
		source_netlist = self.get_cellview_path(self.cellview).find_node('sch.oa')
		# the configuration file for the netlister
		si_env = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'si.env'))
		si_env_copy = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'si.env'))
		# the output netlist
		lvs_netlist_filename = m0.group(1)+'_'+m0.group(2)+'.src.net'
		lvs_netlist = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,lvs_netlist_filename))
		f1 = open(si_env.abspath(),"w")
		f2 = open(si_env_copy.abspath(),"w")
		si_env_content = """
simLibName = "{0}"
simCellName = "{1}"
simViewName = "{2}"
simSimulator = "auCdl"
simNotIncremental = nil
simReNetlistAll = nil
simViewList = '("symbol" "schematic")
simStopList = '("symbol")
simNetlistHier = t
hnlNetlistFileName = "{3}"
simRunDir = "{4}"
resistorModel = " "
shortRES = 2000.0
preserveRES = 'nil
checkRESVAL = 'nil
checkRESSIZE = 'nil
preserveCAP = 'nil
checkCAPVAL = 'nil
checkCAPAREA = 'nil
preserveDIO = 'nil
checkDIOAREA = 'nil
checkDIOPERI = 'nil
displayPININFO = 'nil
preserveALL = 'nil
incFILE = "{5}"
setEQUIV = ""
		""".format(m0.group(1),m0.group(2),m0.group(3),lvs_netlist_filename,self.env.BRICK_RESULTS,getattr(self,'include',''))#'/afs/kip.uni-heidelberg.de/cad/libs/tsmc/cdb/models/hspice/hspice.mdl')#/superfast/home/ahartel/chip-route65/env/include_all_models.scs')
		f1.write(si_env_content)
		f2.write(si_env_content)
		f1.close()
		f2.close()

		aucdl_task = self.create_task('auCdlTask',source_netlist,lvs_netlist)
	else:
		Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_netlist_lvs\'.')





