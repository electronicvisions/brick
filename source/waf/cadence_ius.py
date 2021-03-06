from verilog_scanner import scan_verilog_task
from vhdl_scanner import vhdl_scanner
import os,subprocess, sys, copy
from brick_general import ChattyBrickTask

from waflib import Task, TaskGen, Logs, Errors, Utils

def configure(conf):
	conf.load('brick_general')
	conf.load('cadence_base')

	# check for IUSDIR environment variable
	try:
		conf.env.IUS_DIR = os.environ['IUSDIR']
	except KeyError:
		conf.env.IUS_DIR = os.environ['IUS_DIR']

	# if mixed-signal is enabled, add connectlib
	if conf.env.CDS_MIXED_SIGNAL:
		try:
			conf.env.CDS_LIBS['connectLib'] = os.environ['IUSDIR']+'/tools/affirma_ams/etc/connect_lib/connectLib'
		except TypeError:
			conf.env.CDS_LIBS = {}
			conf.env.CDS_LIBS['connectLib'] = os.environ['IUSDIR']+'/tools/affirma_ams/etc/connect_lib/connectLib'

	conf.env.NCVLOG_LOGFILE = '/ncvlog.log'
	conf.env.NCVHDL_LOGFILE = '/ncvhdl.log'
	conf.env.NCSDFC_LOGFILE = '/ncsdfc.log'
	conf.env.NCELAB_LOGFILE = conf.env.BRICK_LOGFILES+'/ncelab.log'
	conf.env.NCSIM_LOGFILE = conf.env.BRICK_LOGFILES+'/ncsim.log'

	if not conf.env.NCVLOG_OPTIONS:
		conf.env.NCVLOG_OPTIONS = ['-64bit','-use5x']
	if not conf.env.NCVLOG_SV_OPTIONS:
		conf.env.NCVLOG_SV_OPTIONS = ['-64bit','-use5x']
	if not conf.env.NCVLOG_VAMS_OPTIONS:
		conf.env.NCVLOG_VAMS_OPTIONS = ['-64bit','-use5x']
	if not conf.env.NCSDFC_OPTIONS:
		conf.env.NCSDFC_OPTIONS = []
	if not conf.env.NCVHDL_OPTIONS:
		conf.env.NCVHDL_OPTIONS = ['-64bit','-use5x']
	if not conf.env.NCELAB_OPTIONS:
		conf.env.NCELAB_OPTIONS = ['-64bit','-timescale','1ns/10ps']
	if conf.env.CDS_MIXED_SIGNAL:
		conf.env.NCELAB_OPTIONS.extend(['-discipline', 'logic'])
	if not conf.env.NCSIM_OPTIONS:
		conf.env.NCSIM_OPTIONS = ['-64bit','-gui']


	conf.find_program('ncsim',var='CDS_NCSIM')
	conf.find_program('ncelab',var='CDS_NCELAB')
	conf.find_program('ncvlog',var='CDS_NCVLOG')
	conf.find_program('ncvhdl',var='CDS_NCVHDL')


TaskGen.declare_chain(
        rule         = '${CDS_NCVLOG} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.get_logdir_node().abspath()+env.NCVLOG_LOGFILE+gen.name} ${NCVLOG_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = [ '.lib.src',],
        ext_out      = [ '.lib.src.out',],
        reentrant    = False,
        scan         = scan_verilog_task
)
TaskGen.declare_chain(
        rule         = '${CDS_NCVLOG} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.get_logdir_node().abspath()+env.NCVLOG_LOGFILE+gen.name} ${NCVLOG_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = [ '.vp', ],
        ext_out      = [ '.vp.out', ],
        reentrant    = False,
        scan         = scan_verilog_task
)
TaskGen.declare_chain(
        rule         = '${CDS_NCVHDL} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.get_logdir_node().abspath()+env.NCVHDL_LOGFILE+gen.name} ${NCVHDL_OPTIONS} -work ${WORKLIB} ${SRC}',
        ext_in       = ['.vhd'],
        scan         = vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        rule         = '${CDS_NCVHDL} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.get_logdir_node().abspath()+env.NCVHDL_LOGFILE+gen.name} ${NCVHDL_OPTIONS} -work ${WORKLIB} ${SRC}',
        ext_in       = ['.vhdl'],
        scan         = vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        rule         = 'ncsdfc -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.get_logdir_node().abspath()+env.NCSDFC_LOGFILE+gen.name} ${NCSDFC_OPTIONS} ${SRC} -output ${TGT}',
        ext_in       = ['.sdf'],
        ext_out       = ['.sdf.compiled'],
        reentrant    = False,
)

TaskGen.declare_chain(
        rule         = 'ncsdfc -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.get_logdir_node().abspath()+env.NCSDFC_LOGFILE+gen.name} ${NCSDFC_OPTIONS} ${SRC} -output ${TGT}',
        ext_in       = ['.sdf.gz'],
        ext_out       = ['.sdf.compiled'],
        reentrant    = False,
)

class CadenceSvlogTask(Task.Task):
	scan = scan_verilog_task
	run_str = '${CDS_NCVLOG} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.logfile} -sv ${NCVLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${gen.ncvlog_add_options} ${gen.source_string_sv}'

class CadenceVlogTask(Task.Task):
	scan = scan_verilog_task
	run_str = '${CDS_NCVLOG} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.logfile} ${NCVLOG_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${gen.ncvlog_add_options} ${gen.source_string_v}'

class CadenceVamslogTask(Task.Task):
	scan = scan_verilog_task
	run_str = '${CDS_NCVLOG} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${gen.logfile} -ams ${NCVLOG_VAMS_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${gen.ncvlog_add_options} ${gen.source_string_vams}'



@TaskGen.before('process_source')
@TaskGen.feature('cds_compile_hdl')
def cds_ius_prepare(self):
	# save worklib to env
	self.env.WORKLIB = getattr(self,'worklib',self.env.CDS_WORKLIB)
	# create task to generate worklib (if necessary)
	self.check_create_worklib_task(self.env.WORKLIB)
	#
	# transform search paths to the format used for ncvlog
	#
	vsp = getattr(self,'verilog_search_paths',[])
	self.env.VERILOG_SEARCH_PATHS = []
	vid = []
	if len(vsp) > 0:
		for path in vsp:
			self.env.VERILOG_SEARCH_PATHS.append(path.abspath())
			vid.append('-INCDIR')
			vid.append(path.abspath())

	if len(vid) > 0:
		self.env.VERILOG_INC_DIRS = vid

	if not hasattr(self,'name'):
		self.name = Node.split_path(self.source[0])[-1]

	if not hasattr(self,'source'):
		raise Errors.ConfigurationError('Please specify the source attribute for task generator '+getattr(self,'name','?noname? (and give it a name, too!)'))

	# generate the logfile name
	self.logfile = self.get_logdir_node().make_node(self.env.NCVLOG_LOGFILE+'_'+self.name).abspath()

	# process source here, skip default process_source
	self.source_vams = []
	self.source_string_vams = []
	self.source_sv   = []
	self.source_string_sv   = []
	self.source_v    = []
	self.source_string_v    = []
	remove_sources = []
	for src in getattr(self,'source',[]):
		if src.suffix() == '.vams' or src.suffix() == '.va':
			self.source_string_vams.append(src.abspath())
			self.source_vams.append(src)
			remove_sources.append(src)
		elif src.suffix() == '.v':
			self.source_string_v.append(src.abspath())
			self.source_v.append(src)
			remove_sources.append(src)
		elif src.suffix() == '.sv':
			self.source_string_sv.append(src.abspath())
			self.source_sv.append(src)
			remove_sources.append(src)

	for src in remove_sources:
		self.source.remove(src)
	#print self.name
	#print len(self.source_string_vams), len(self.source_string_v), len(self.source_string_sv)

	if hasattr(self,'view'):
		self.ncvlog_add_options = ['-VIEW',self.view]
	else:
		self.ncvlog_add_options = []

	if len(self.source_string_vams) > 0:
		task = self.create_task("CadenceVamslogTask",self.source_vams,[])
	if len(self.source_string_v) > 0:
		task = self.create_task("CadenceVlogTask",self.source_v,[])
	if len(self.source_string_sv) > 0:
		task = self.create_task("CadenceSvlogTask",self.source_sv,[])


#
# Elaboration and Simulation tasks
#

@Task.always_run
class ncelabTask(ChattyBrickTask):
	run_str  = '${CDS_NCELAB} ${gen.simulation_toplevel} ${gen.bindings} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${NCELAB_LOGFILE} ${NCELAB_OPTIONS} '
	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('ncelab: *E') == 0:
				Logs.error("Error in line %d: %s" % (num,line[10:]))
				ret = 1
			elif line.find('ncelab: *F') == 0:
				Logs.error("Error in line %d: %s" % (num,line[10:]))
				ret = 1

		return ret


@TaskGen.feature('cds_elab')
def cds_ius_elaborate(self):
	try:
		self.simulation_toplevel = self.toplevel
	except AttributeError:
		Logs.error('Please name a toplevel unit for elaboration with feature \'cds_elab\'')
		return -1

	self.bindings = []
	for bind in getattr(self,'binding',[]):
		self.bindings.extend(['-binding',bind])

	if getattr(self,'primary',False):
		self.bindings.append('-mkprimsnap')

	self.create_task("ncelabTask")



@Task.always_run
class ncsimTask(ChattyBrickTask):
	shell = True
	run_str = '${CDS_NCSIM} -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -logfile ${NCSIM_LOGFILE} ${SIMULATION_TOPLEVEL} ${NCSIM_OPTIONS} ${gen.ANALOG_CONTROL}'


@TaskGen.feature('ncsim')
def ncsim_run(self):
	self.env.SIMULATION_TOPLEVEL = self.toplevel
	self.ANALOG_CONTROL = ''
	if self.bld.env.CDS_MIXED_SIGNAL:
		# create amsControl.scs
		analog_control_file = self.path.get_bld().make_node('amsControl.scs')
		f = open(analog_control_file.abspath(),'w')
		if hasattr(self,'analysis'):
			f.write(self.analysis+'\n')
		else:
			stop_time = getattr(self,'stop_time','100u')
			f.write('tran tran stop='+stop_time+'\n')
		for line in getattr(self,'analog_control_mixin',[]):
			f.write(line+'\n')
		f.close()
		self.ANALOG_CONTROL = '-analogControl '+analog_control_file.abspath()

	self.create_task('ncsimTask',None,None)

# vim: noexpandtab:
